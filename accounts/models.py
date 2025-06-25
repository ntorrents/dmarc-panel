from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Empresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150, unique=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Role(models.Model):
    ROLE_TYPES = [
        ('super_admin', 'Super Admin'),
        ('company_admin', 'Company Admin'),
        ('config_user', 'Configuration User'),
        ('read_only', 'Read Only User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, choices=ROLE_TYPES, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    permisos = models.JSONField(default=dict, help_text="Specific permissions for this role")
    
    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['nombre']

    def __str__(self):
        return self.get_nombre_display()

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        Empresa, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='usuarios'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='usuarios',
        null=True,
        blank=True
    )
    email = models.EmailField(unique=True)
    activo = models.BooleanField(default=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"

    @property
    def is_super_admin(self):
        return self.role and self.role.nombre == 'super_admin'

    @property
    def is_company_admin(self):
        return self.role and self.role.nombre == 'company_admin'

    @property
    def can_edit_config(self):
        return self.role and self.role.nombre in ['super_admin', 'company_admin', 'config_user']

    @property
    def is_read_only(self):
        return self.role and self.role.nombre == 'read_only'

    def has_company_access(self, empresa_id):
        """Check if user has access to a specific company"""
        if self.is_super_admin:
            return True
        return str(self.empresa.id) == str(empresa_id) if self.empresa else False