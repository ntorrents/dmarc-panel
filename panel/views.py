from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from .models import Dominio, DNSRecord, Tag, AuditLog, SystemSetting
from .serializers import (
    DominioSerializer, DominioListSerializer, DNSRecordSerializer,
    TagSerializer, AuditLogSerializer, SystemSettingSerializer,
    BulkDomainUpdateSerializer, BulkDNSRecordCreateSerializer
)
from .permissions import CanManageDomain, CanManageCompanyData, IsReadOnlyOrCanEdit
from .utils import log_audit_event, get_client_ip
from accounts.permissions import IsSuperAdmin

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageCompanyData]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return Tag.objects.all()
        elif user.empresa:
            return Tag.objects.filter(empresa=user.empresa)
        return Tag.objects.none()

    def perform_create(self, serializer):
        tag = serializer.save()
        log_audit_event(
            user=self.request.user,
            action='create',
            content_object=tag,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

class DominioViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanManageDomain]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['activo', 'status', 'compliance_level', 'dmarc_policy', 'tags']
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'creado_en', 'actualizado_en', 'last_dns_check']
    ordering = ['-creado_en']

    def get_serializer_class(self):
        if self.action == 'list':
            return DominioListSerializer
        return DominioSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Dominio.objects.select_related('empresa').prefetch_related('tags', 'registros')
        
        if user.is_super_admin:
            return queryset
        elif user.empresa:
            return queryset.filter(empresa=user.empresa)
        return Dominio.objects.none()

    def perform_create(self, serializer):
        dominio = serializer.save()
        log_audit_event(
            user=self.request.user,
            action='create',
            content_object=dominio,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_values = DominioSerializer(old_instance).data
        dominio = serializer.save()
        new_values = DominioSerializer(dominio).data
        
        log_audit_event(
            user=self.request.user,
            action='update',
            content_object=dominio,
            changes={'old': old_values, 'new': new_values},
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    @action(detail=True, methods=['get'])
    def dns_records(self, request, pk=None):
        """Get all DNS records for a specific domain"""
        dominio = self.get_object()
        records = dominio.registros.all()
        serializer = DNSRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def check_dns(self, request, pk=None):
        """Trigger DNS check for a specific domain"""
        dominio = self.get_object()
        # This would trigger a Celery task in a real implementation
        dominio.dns_check_status = 'checking'
        dominio.save()
        
        log_audit_event(
            user=self.request.user,
            action='dns_check',
            content_object=dominio,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'DNS check initiated'})

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple domains"""
        serializer = BulkDomainUpdateSerializer(data=request.data)
        if serializer.is_valid():
            domain_ids = serializer.validated_data['domain_ids']
            updates = serializer.validated_data['updates']
            
            # Check permissions for all domains
            domains = self.get_queryset().filter(id__in=domain_ids)
            if len(domains) != len(domain_ids):
                return Response(
                    {'error': 'Some domains not found or access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Perform bulk update
            updated_count = domains.update(**updates)
            
            log_audit_event(
                user=self.request.user,
                action='bulk_operation',
                changes={'operation': 'bulk_update', 'domain_ids': domain_ids, 'updates': updates},
                ip_address=get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'updated_count': updated_count})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get domain statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_dominios': queryset.count(),
            'dominios_activos': queryset.filter(activo=True).count(),
            'por_status': {},
            'por_compliance': {},
            'por_dmarc_policy': {}
        }
        
        # Status distribution
        for choice in Dominio.STATUS_CHOICES:
            count = queryset.filter(status=choice[0]).count()
            stats['por_status'][choice[0]] = count
        
        # Compliance distribution
        for choice in Dominio.COMPLIANCE_CHOICES:
            count = queryset.filter(compliance_level=choice[0]).count()
            stats['por_compliance'][choice[0]] = count
        
        # DMARC policy distribution
        for choice in Dominio.DMARC_POLICY_CHOICES:
            count = queryset.filter(dmarc_policy=choice[0]).count()
            stats['por_dmarc_policy'][choice[0]] = count
        
        return Response(stats)

class DNSRecordViewSet(viewsets.ModelViewSet):
    serializer_class = DNSRecordSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDomain]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estado', 'dominio', 'ttl']
    search_fields = ['nombre', 'valor', 'dominio__nombre']
    ordering_fields = ['tipo', 'nombre', 'creado_en', 'ultima_comprobacion']
    ordering = ['-creado_en']

    def get_queryset(self):
        user = self.request.user
        queryset = DNSRecord.objects.select_related('dominio', 'creado_por')
        
        if user.is_super_admin:
            return queryset
        elif user.empresa:
            return queryset.filter(dominio__empresa=user.empresa)
        return DNSRecord.objects.none()

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)
        
        log_audit_event(
            user=self.request.user,
            action='create',
            content_object=serializer.instance,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_values = DNSRecordSerializer(old_instance).data
        record = serializer.save()
        new_values = DNSRecordSerializer(record).data
        
        log_audit_event(
            user=self.request.user,
            action='update',
            content_object=record,
            changes={'old': old_values, 'new': new_values},
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create DNS records for a domain"""
        serializer = BulkDNSRecordCreateSerializer(data=request.data)
        if serializer.is_valid():
            domain_id = serializer.validated_data['domain_id']
            records_data = serializer.validated_data['records']
            
            # Check domain access
            try:
                dominio = Dominio.objects.get(id=domain_id)
                self.check_object_permissions(request, dominio)
            except Dominio.DoesNotExist:
                return Response(
                    {'error': 'Domain not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create records
            created_records = []
            for record_data in records_data:
                record_data['dominio'] = domain_id
                record_data['creado_por'] = request.user.id
                record_serializer = DNSRecordSerializer(data=record_data)
                if record_serializer.is_valid():
                    record = record_serializer.save()
                    created_records.append(record)
                else:
                    return Response(record_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            log_audit_event(
                user=self.request.user,
                action='bulk_operation',
                content_object=dominio,
                changes={'operation': 'bulk_create_records', 'count': len(created_records)},
                ip_address=get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'created_count': len(created_records),
                'records': DNSRecordSerializer(created_records, many=True).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'content_type', 'user', 'empresa']
    search_fields = ['object_repr', 'user__username', 'user__email']
    ordering = ['-timestamp']

    def get_queryset(self):
        user = self.request.user
        queryset = AuditLog.objects.select_related('user', 'content_type', 'empresa')
        
        if user.is_super_admin:
            return queryset
        elif user.empresa:
            return queryset.filter(empresa=user.empresa)
        return AuditLog.objects.none()

class SystemSettingViewSet(viewsets.ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['value_type', 'is_sensitive']
    search_fields = ['key', 'description']
    ordering = ['key']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Show sensitive values only to superusers
        context['show_sensitive'] = self.request.user.is_superuser
        return context

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        
        log_audit_event(
            user=self.request.user,
            action='update',
            content_object=serializer.instance,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )