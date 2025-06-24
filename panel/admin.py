from django.contrib import admin
from .models import Cliente, Dominio, DNSRecord, Tag, DominioUsuarioAcceso
from django.contrib.auth import get_user_model
User = get_user_model()

from django.contrib.auth.admin import UserAdmin

admin.site.register(User, UserAdmin)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'empresa')
    search_fields = ('nombre', 'email', 'empresa')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente', 'activo', 'compliance_level', 'dmarc_policy', 'creado_en')
    list_filter = ('activo', 'compliance_level', 'dmarc_policy')
    search_fields = ('nombre',)
    autocomplete_fields = ('cliente', 'tags')
    filter_horizontal = ('tags',)


@admin.register(DNSRecord)
class RegistroDNSAdmin(admin.ModelAdmin):
    list_display = ('dominio', 'tipo', 'estado', 'ultima_comprobacion')
    list_filter = ('tipo', 'estado')
    search_fields = ('dominio__nombre', 'valor')


@admin.register(DominioUsuarioAcceso)
class DominioUsuarioAccesoAdmin(admin.ModelAdmin):
    list_display = ('user', 'dominio', 'rol')
    list_filter = ('rol',)
    search_fields = ('user__username', 'dominio__nombre')
    autocomplete_fields = ('user', 'dominio')
