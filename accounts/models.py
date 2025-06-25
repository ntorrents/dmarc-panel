# accounts/models.py (si tienes una app accounts para usuarios)

from django.contrib.auth.models import AbstractUser
from django.db import models

class Empresa(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    direccion = models.TextField(blank=True, null=True)
    # otros campos...

    def __str__(self):
        return self.nombre

class User(AbstractUser):
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 


