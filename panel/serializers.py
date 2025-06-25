from rest_framework import serializers
from .models import Dominio, DNSRecord, Tag, AuditLog, SystemSetting
from accounts.models import User, Empresa

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'nombre', 'color', 'descripcion', 'empresa', 'creado_en']
        read_only_fields = ['id', 'creado_en']

    def validate(self, data):
        # Ensure tag belongs to user's company (unless super admin)
        request = self.context.get('request')
        if request and request.user:
            if not request.user.is_super_admin:
                if request.user.empresa:
                    data['empresa'] = request.user.empresa
                else:
                    raise serializers.ValidationError("Usuario debe pertenecer a una empresa")
        return data

class DominioListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    total_dns_records = serializers.ReadOnlyField()
    valid_dns_records = serializers.ReadOnlyField()

    class Meta:
        model = Dominio
        fields = [
            'id', 'nombre', 'activo', 'status', 'compliance_level', 'dmarc_policy',
            'empresa', 'empresa_nombre', 'tags', 'creado_en', 'actualizado_en',
            'total_dns_records', 'valid_dns_records', 'last_dns_check', 'dns_check_status'
        ]

class DominioSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        many=True, 
        required=False
    )
    tags_details = TagSerializer(source='tags', many=True, read_only=True)
    total_dns_records = serializers.ReadOnlyField()
    valid_dns_records = serializers.ReadOnlyField()

    class Meta:
        model = Dominio
        fields = [
            'id', 'empresa', 'empresa_nombre', 'nombre', 'activo', 'status',
            'compliance_level', 'dmarc_policy', 'dns_provider', 'dns_provider_zone_id',
            'tags', 'tags_details', 'notification_email', 'notify_on_changes', 
            'notify_on_expiration', 'creado_en', 'actualizado_en', 'last_dns_check', 
            'dns_check_status', 'expiration_date', 'total_dns_records', 'valid_dns_records'
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en', 'last_dns_check', 'dns_check_status']

    def validate_nombre(self, value):
        """Validate domain name format"""
        import re
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, value):
            raise serializers.ValidationError("Formato de dominio inválido")
        return value.lower()

    def validate(self, data):
        # Ensure domain belongs to user's company (unless super admin)
        request = self.context.get('request')
        if request and request.user:
            if not request.user.is_super_admin:
                if request.user.empresa:
                    data['empresa'] = request.user.empresa
                else:
                    raise serializers.ValidationError("Usuario debe pertenecer a una empresa")
        return data

    def validate_tags(self, tags):
        """Ensure tags belong to the same company as the domain"""
        request = self.context.get('request')
        if request and request.user and not request.user.is_super_admin:
            user_empresa = request.user.empresa
            if user_empresa:
                for tag in tags:
                    if tag.empresa != user_empresa:
                        raise serializers.ValidationError(
                            f"Tag '{tag.nombre}' no pertenece a tu empresa"
                        )
        return tags

class DNSRecordSerializer(serializers.ModelSerializer):
    dominio_nombre = serializers.CharField(source='dominio.nombre', read_only=True)
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = DNSRecord
        fields = [
            'id', 'dominio', 'dominio_nombre', 'tipo', 'nombre', 'valor', 'ttl', 'prioridad',
            'estado', 'ultima_comprobacion', 'error_message', 'selector', 'policy',
            'creado_en', 'actualizado_en', 'creado_por', 'creado_por_username'
        ]
        read_only_fields = ['id', 'ultima_comprobacion', 'creado_en', 'actualizado_en']

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

class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_username', 'user_email', 'empresa', 'empresa_nombre',
            'action', 'timestamp', 'content_type', 'content_type_name', 'object_id', 
            'object_repr', 'changes', 'ip_address', 'user_agent'
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
        read_only_fields = ['id', 'created_at', 'updated_at']

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
        child=serializers.UUIDField(),
        min_length=1
    )
    updates = serializers.DictField()

class BulkDNSRecordCreateSerializer(serializers.Serializer):
    domain_id = serializers.UUIDField()
    records = DNSRecordSerializer(many=True)

    def validate_domain_id(self, value):
        if not Dominio.objects.filter(id=value).exists():
            raise serializers.ValidationError("Dominio no encontrado")
        return value