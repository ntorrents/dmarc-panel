from django.db import models
from accounts.models import User  # Importa el modelo de usuario personalizado

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    empresa = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Tag(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Dominio(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='dominios')
    nombre = models.CharField(max_length=255, unique=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='dominios')

    # Punto 3: Compliance y política DMARC
    compliance_level = models.CharField(
        max_length=50,
        choices=[
            ('none', 'None'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='none'
    )

    dmarc_policy = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('quarantine', 'Quarantine'),
            ('reject', 'Reject'),
        ],
        default='none'
    )

    def __str__(self):
        return self.nombre

class DNSRecord(models.Model):
    TIPO_CHOICES = [
        ('SPF', 'SPF'),
        ('DKIM', 'DKIM'),
        ('DMARC', 'DMARC'),
    ]

    dominio = models.ForeignKey(Dominio, on_delete=models.CASCADE, related_name='registros')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.TextField()
    estado = models.CharField(max_length=50, default='Pendiente')  # válido, inválido, error, etc.
    ultima_comprobacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dominio.nombre} - {self.tipo}"

# Punto 4: Acceso de usuarios a dominios con rol
class DominioUsuarioAcceso(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dominio = models.ForeignKey(Dominio, on_delete=models.CASCADE)

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    class Meta:
        unique_together = ('user', 'dominio')

    def __str__(self):
        return f"{self.user.username} - {self.dominio.nombre} ({self.rol})"
