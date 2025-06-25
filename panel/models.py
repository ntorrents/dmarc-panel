from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from accounts.models import User, Empresa
import uuid
import json

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#007bff', help_text="Color en formato hexadecimal")
    descripcion = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tags')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['nombre']
        unique_together = ['nombre', 'empresa']

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"

class Dominio(models.Model):
    COMPLIANCE_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    DMARC_POLICY_CHOICES = [
        ('none', 'None'),
        ('quarantine', 'Quarantine'),
        ('reject', 'Reject'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='dominios')
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='dominios')

    # DMARC Configuration
    compliance_level = models.CharField(
        max_length=50,
        choices=COMPLIANCE_CHOICES,
        default='none'
    )
    dmarc_policy = models.CharField(
        max_length=20,
        choices=DMARC_POLICY_CHOICES,
        default='none'
    )

    # DNS Provider Integration
    dns_provider = models.CharField(max_length=50, blank=True, null=True)
    dns_provider_zone_id = models.CharField(max_length=100, blank=True, null=True)

    # Monitoring
    last_dns_check = models.DateTimeField(blank=True, null=True)
    dns_check_status = models.CharField(max_length=50, default='pending')
    expiration_date = models.DateField(blank=True, null=True)

    # Notifications
    notification_email = models.EmailField(blank=True, null=True)
    notify_on_changes = models.BooleanField(default=True)
    notify_on_expiration = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
        ordering = ['-creado_en']
        unique_together = ['nombre', 'empresa']

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"

    @property
    def total_dns_records(self):
        return self.registros.count()

    @property
    def valid_dns_records(self):
        return self.registros.filter(estado='valid').count()

class DNSRecord(models.Model):
    TIPO_CHOICES = [
        ('SPF', 'SPF'),
        ('DKIM', 'DKIM'),
        ('DMARC', 'DMARC'),
        ('MX', 'MX'),
        ('TXT', 'TXT'),
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('CNAME', 'CNAME'),
    ]

    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('pending', 'Pending'),
        ('error', 'Error'),
        ('warning', 'Warning'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dominio = models.ForeignKey(Dominio, on_delete=models.CASCADE, related_name='registros')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=255, help_text="Nombre del registro (ej: @, www, mail)")
    valor = models.TextField()
    ttl = models.PositiveIntegerField(default=3600, help_text="Time To Live en segundos")
    prioridad = models.PositiveIntegerField(blank=True, null=True, help_text="Solo para registros MX")
    
    # Status and monitoring
    estado = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    ultima_comprobacion = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)
    
    # DKIM specific fields
    selector = models.CharField(max_length=100, blank=True, null=True, help_text="Solo para DKIM")
    
    # DMARC specific fields
    policy = models.CharField(max_length=10, blank=True, null=True, help_text="Solo para DMARC")
    
    # Metadata
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Registro DNS"
        verbose_name_plural = "Registros DNS"
        ordering = ['-actualizado_en']
        unique_together = ['dominio', 'tipo', 'nombre']

    def __str__(self):
        return f"{self.dominio.nombre} - {self.tipo} ({self.nombre})"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('dns_check', 'DNS Check'),
        ('bulk_operation', 'Bulk Operation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Generic foreign key to track any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)  # Changed to CharField for UUID support
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional details
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.object_repr} ({self.timestamp})"

    def set_changes(self, old_values, new_values):
        """Helper method to set changes as a dictionary"""
        changes = {}
        for field, new_value in new_values.items():
            old_value = old_values.get(field)
            if old_value != new_value:
                changes[field] = {
                    'old': old_value,
                    'new': new_value
                }
        self.changes = changes

class SystemSetting(models.Model):
    VALUE_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES, default='string')
    description = models.TextField(blank=True, null=True)
    is_sensitive = models.BooleanField(default=False, help_text="Marca si contiene información sensible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ['key']

    def __str__(self):
        return self.key

    def get_value(self):
        """Return the value converted to the appropriate type"""
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            return json.loads(self.value)
        return self.value

    def set_value(self, value):
        """Set the value, converting it to string for storage"""
        if self.value_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)