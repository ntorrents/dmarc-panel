from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserProfileSerializer,
    EmpresaSerializer, RoleSerializer
)
from .models import Empresa, Role
from panel.utils import log_audit_event, get_client_ip
from .permissions import IsSuperAdmin, IsCompanyAdminOrSuperAdmin

User = get_user_model()

class AuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        action = request.data.get('action')
        
        if action == 'login':
            return self.login(request)
        elif action == 'logout':
            return self.logout(request)
        elif action == 'refresh':
            return self.refresh_token(request)
        else:
            return Response(
                {'error': 'Invalid action'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email y contraseña son requeridos'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request=request, email=email, password=password)
        if not user or not user.activo:
            return Response(
                {'error': 'Credenciales inválidas o cuenta deshabilitada'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Update last access
        user.ultimo_acceso = datetime.now()
        user.save(update_fields=['ultimo_acceso'])

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Create response
        response = Response({
            'message': 'Login exitoso',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)

        # Set HttpOnly cookies
        response.set_cookie(
            'access_token',
            str(access_token),
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
            samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
        )
        
        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
            samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
        )

        # Log audit event
        log_audit_event(
            user=user,
            action='login',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return response

    def logout(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except TokenError:
            pass

        # Log audit event if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            log_audit_event(
                user=request.user,
                action='logout',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        response = Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)
        
        # Clear cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response

    def refresh_token(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token no encontrado'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token

            response = Response({
                'message': 'Token renovado exitosamente'
            }, status=status.HTTP_200_OK)

            # Set new access token cookie
            response.set_cookie(
                'access_token',
                str(access_token),
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=settings.SIMPLE_JWT.get('AUTH_COOKIE_SECURE', False),
                samesite=settings.SIMPLE_JWT.get('AUTH_COOKIE_SAMESITE', 'Lax')
            )

            return response

        except TokenError:
            return Response(
                {'error': 'Token inválido'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class RegisterView(APIView):
    permission_classes = [IsCompanyAdminOrSuperAdmin]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Validate company access for non-super admins
            if not request.user.is_super_admin:
                empresa_id = serializer.validated_data.get('empresa')
                if empresa_id and not request.user.has_company_access(empresa_id.id):
                    return Response(
                        {'error': 'No tienes permisos para crear usuarios en esta empresa'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

            user = serializer.save()
            
            log_audit_event(
                user=request.user,
                action='create',
                content_object=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'message': 'Usuario registrado correctamente',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            old_data = UserProfileSerializer(request.user).data
            user = serializer.save()
            new_data = UserProfileSerializer(user).data
            
            log_audit_event(
                user=request.user,
                action='update',
                content_object=user,
                changes={'old': old_data, 'new': new_data},
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response(new_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmpresaViewSet(viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsSuperAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return self.queryset
        elif user.empresa:
            return self.queryset.filter(id=user.empresa.id)
        return Empresa.objects.none()

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsSuperAdmin]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('empresa', 'role')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [IsCompanyAdminOrSuperAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsCompanyAdminOrSuperAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return self.queryset
        elif user.empresa:
            return self.queryset.filter(empresa=user.empresa)
        return User.objects.none()

    def perform_create(self, serializer):
        # Validate company access for non-super admins
        if not self.request.user.is_super_admin:
            empresa = serializer.validated_data.get('empresa')
            if empresa and not self.request.user.has_company_access(empresa.id):
                raise permissions.PermissionDenied(
                    'No tienes permisos para crear usuarios en esta empresa'
                )

        user = serializer.save()
        log_audit_event(
            user=self.request.user,
            action='create',
            content_object=user,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        
        # Validate company access for non-super admins
        if not self.request.user.is_super_admin:
            if not self.request.user.has_company_access(old_instance.empresa.id):
                raise permissions.PermissionDenied(
                    'No tienes permisos para editar este usuario'
                )

        old_values = UserSerializer(old_instance).data
        user = serializer.save()
        new_values = UserSerializer(user).data
        
        log_audit_event(
            user=self.request.user,
            action='update',
            content_object=user,
            changes={'old': old_values, 'new': new_values},
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )