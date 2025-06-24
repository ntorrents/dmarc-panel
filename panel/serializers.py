from rest_framework import serializers
from .models import Cliente, Dominio, DNSRecord, Tag, DominioUsuarioAcceso, AuditLog, SystemSetting
from accounts.models import User

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'nombre', 'color', 'descripcion']

class ClienteSerializer(serializers.ModelSerializer):
    total_dominios = serializers.SerializerMethodField()
    dominios_activos = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre', 'email', 'empresa', 'telefono', 'direccion',
            'activo', 'creado_en', 'actualizado_en', 'total_dominios', 'dominios_activos'
        ]
        read_only_fields = ['creado_en', 'actualizado_en']

    def get_total_dominios(self, obj):
        return obj.dominios.count()

    def get_dominios_activos(self, obj):
        return obj.dominios.filter(activo=True).count()

class DominioListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    cliente_empresa = serializers.CharField(source='cliente.empresa', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    total_dns_records = serializers.ReadOnlyField()
    valid_dns_records = serializers.ReadOnlyField()

    class Meta:
        model = Dominio
        fields = [
            'id', 'nombre', 'activo', 'status', 'compliance_level', 'dmarc_policy',
            'cliente_nombre', 'cliente_empresa', 'tags', 'creado_en', 'actualizado_en',
            'total_dns_records', 'valid_dns_records', 'last_dns_check', 'dns_check_status'
        ]

class DominioSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    cliente_details = ClienteSerializer(source='cliente', read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    tags_details = TagSerializer(source='tags', many=True, read_only=True)
    total_dns_records = serializers.ReadOnlyField()
    valid_dns_records = serializers.ReadOnlyField()

    class Meta:
        model = Dominio
        fields = [
            'id', 'cliente', 'cliente_details', 'nombre', 'activo', 'status',
            'compliance_level', 'dmarc_policy', 'dns_provider', 'dns_provider_zone_id',
            'tags', 'tags_details', 'notification_email', 'notify_on_changes', 'notify_on_expiration',
            'creado_en', 'actualizado_en', 'last_dns_check', 'dns_check_status',
            'expiration_date', 'total_dns_records', 'valid_dns_records'
        ]
        read_only_fields = ['creado_en', 'actualizado_en', 'last_dns_check', 'dns_check_status']

    def validate_nombre(self, value):
        """Validate domain name format"""
        import re
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, value):
            raise serializers.ValidationError("Formato de dominio inválido")
        return value.lower()

class DNSRecordSerializer(serializers.ModelSerializer):
    dominio = serializers.PrimaryKeyRelatedField(queryset=Dominio.objects.all())
    dominio_nombre = serializers.CharField(source='dominio.nombre', read_only=True)
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = DNSRecord
        fields = [
            'id', 'dominio', 'dominio_nombre', 'tipo', 'nombre', 'valor', 'ttl', 'prioridad',
            'estado', 'ultima_comprobacion', 'error_message', 'selector', 'policy',
            'creado_en', 'actualizado_en', 'creado_por', 'creado_por_username'
        ]
        read_only_fields = ['ultima_comprobacion', 'creado_en', 'actualizado_en']

    def validate(self, data):
        """Custom validation for DNS records"""
        tipo = data.get('tipo')
        valor = data.get('valor')
        
        if tipo == 'MX' and not data.get('prioridad'):
            raise serializers.ValidationError("Los registros MX requieren prioridad")
        
        if tipo == 'DKIM' and not data.get('selector'):
            raise serializers.ValidationError("Los registros DKIM requieren selector")
        
        # Basic validation for common record types
        if tipo == 'A':
            import ipaddress
            try:
                ipaddress.IPv4Address(valor)
            except ipaddress.AddressValueError:
                raise serializers.ValidationError("Dirección IPv4 inválida para registro A")
        
        if tipo == 'AAAA':
            import ipaddress
            try:
                ipaddress.IPv6Address(valor)
            except ipaddress.AddressValueError:
                raise serializers.ValidationError("Dirección IPv6 inválida para registro AAAA")
        
        return data

class DominioUsuarioAccesoSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user_details = serializers.SerializerMethodField()
    dominio = serializers.PrimaryKeyRelatedField(queryset=Dominio.objects.all())
    dominio_nombre = serializers.CharField(source='dominio.nombre', read_only=True)
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = DominioUsuarioAcceso
        fields = [
            'id', 'user', 'user_details', 'dominio', 'dominio_nombre', 'rol',
            'creado_en', 'creado_por', 'creado_por_username'
        ]
        read_only_fields = ['creado_en']

    def get_user_details(self, obj):
        return {
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_username', 'action', 'timestamp', 'content_type',
            'content_type_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['timestamp']

class SystemSettingSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    display_value = serializers.SerializerMethodField()

    class Meta:
        model = SystemSetting
        fields = [
            'id', 'key', 'value', 'value_type', 'description', 'is_sensitive',
            'created_at', 'updated_at', 'updated_by', 'updated_by_username', 'display_value'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_display_value(self, obj):
        """Return masked value for sensitive settings"""
        if obj.is_sensitive:
            return "***HIDDEN***"
        return obj.get_value()

    def to_representation(self, instance):
        """Hide sensitive values in API responses"""
        data = super().to_representation(instance)
        if instance.is_sensitive and not self.context.get('show_sensitive', False):
            data['value'] = "***HIDDEN***"
        return data

# Bulk operation serializers
class BulkDomainUpdateSerializer(serializers.Serializer):
    domain_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    updates = serializers.DictField()

class BulkDNSRecordCreateSerializer(serializers.Serializer):
    domain_id = serializers.IntegerField()
    records = DNSRecordSerializer(many=True)

    def validate_domain_id(self, value):
        if not Dominio.objects.filter(id=value).exists():
            raise serializers.ValidationError("Dominio no encontrado")
        return value