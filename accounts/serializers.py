from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Empresa, Role

User = get_user_model()

class EmpresaSerializer(serializers.ModelSerializer):
    total_usuarios = serializers.SerializerMethodField()
    total_dominios = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = [
            'id', 'nombre', 'direccion', 'activo', 'creado_en', 
            'actualizado_en', 'total_usuarios', 'total_dominios'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']

    def get_total_usuarios(self, obj):
        return obj.usuarios.filter(activo=True).count()

    def get_total_dominios(self, obj):
        return getattr(obj, 'total_dominios', 0)

class RoleSerializer(serializers.ModelSerializer):
    total_usuarios = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'nombre', 'descripcion', 'permisos', 'total_usuarios']
        read_only_fields = ['id']

    def get_total_usuarios(self, obj):
        return obj.usuarios.filter(activo=True).count()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 
            'first_name', 'last_name', 'empresa', 'role'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    full_name = serializers.SerializerMethodField()
    computed_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'empresa', 'empresa_nombre', 'activo', 
            'date_joined', 'last_login', 'ultimo_acceso',
            'computed_role'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'ultimo_acceso']

    def get_computed_role(self, obj):
        if obj.is_superuser:
            return "super_admin"
        elif obj.is_staff:
            return "client_admin"
        else:
            return "user"

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user's own profile"""
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    permissions = serializers.SerializerMethodField()
    computed_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'empresa', 'empresa_nombre', 'permissions', 'computed_role'
        ]
        read_only_fields = ['id', 'empresa']

    def get_permissions(self, obj):
        return {
            'is_super_admin': bool(obj.is_super_admin),
            'is_company_admin': bool(obj.is_company_admin),
            'can_edit_config': bool(obj.can_edit_config),
            'is_read_only': bool(obj.is_read_only),
        }

    def get_computed_role(self, obj):
        if obj.is_superuser:
            return "super_admin"
        elif obj.is_staff:
            return "client_admin"
        else:
            return "user"

