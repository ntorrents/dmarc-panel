from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Dominio, DNSRecord, Tag, AuditLog, SystemSetting
from accounts.models import Empresa

User = get_user_model()

# Register the custom User model
admin.site.register(User, UserAdmin)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_display', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('color',)

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'total_dominios', 'creado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('nombre', 'direccion')
    readonly_fields = ('creado_en', 'actualizado_en')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activo')
        }),
        ('Contacto', {
            'fields': ('direccion',)
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

    def total_dominios(self, obj):
        count = obj.dominios.count()
        if count > 0:
            url = reverse('admin:panel_dominio_changelist') + f'?empresa__id__exact={obj.id}'
            return format_html('<a href="{}">{} dominios</a>', url, count)
        return '0 dominios'
    total_dominios.short_description = 'Total Dominios'

@admin.register(Dominio)
class DominioAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'empresa', 'status', 'activo', 'compliance_level', 
        'dmarc_policy', 'total_records', 'last_dns_check', 'creado_en'
    )
    list_filter = (
        'activo', 'status', 'compliance_level', 'dmarc_policy', 
        'dns_provider', 'notify_on_changes', 'creado_en'
    )
    search_fields = ('nombre', 'empresa__nombre')
    autocomplete_fields = ('empresa',)
    filter_horizontal = ('tags',)
    readonly_fields = ('creado_en', 'actualizado_en', 'last_dns_check', 'dns_check_status')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa', 'nombre', 'activo', 'status')
        }),
        ('Configuración DMARC', {
            'fields': ('compliance_level', 'dmarc_policy')
        }),
        ('DNS Provider', {
            'fields': ('dns_provider', 'dns_provider_zone_id'),
            'classes': ('collapse',)
        }),
        ('Notificaciones', {
            'fields': ('notification_email', 'notify_on_changes', 'notify_on_expiration', 'expiration_date')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Monitoreo', {
            'fields': ('last_dns_check', 'dns_check_status'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

    def total_records(self, obj):
        count = obj.registros.count()
        if count > 0:
            url = reverse('admin:panel_dnsrecord_changelist') + f'?dominio__id__exact={obj.id}'
            return format_html('<a href="{}">{} registros</a>', url, count)
        return '0 registros'
    total_records.short_description = 'DNS Records'

@admin.register(DNSRecord)
class DNSRecordAdmin(admin.ModelAdmin):
    list_display = (
        'dominio', 'tipo', 'nombre', 'estado', 'ttl', 'prioridad', 
        'ultima_comprobacion', 'creado_por'
    )
    list_filter = ('tipo', 'estado', 'ttl', 'creado_en', 'ultima_comprobacion')
    search_fields = ('dominio__nombre', 'nombre', 'valor')
    autocomplete_fields = ('dominio', 'creado_por')
    readonly_fields = ('creado_en', 'actualizado_en', 'ultima_comprobacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('dominio', 'tipo', 'nombre', 'valor', 'ttl')
        }),
        ('Configuración Específica', {
            'fields': ('prioridad', 'selector', 'policy'),
            'description': 'Campos específicos según el tipo de registro'
        }),
        ('Estado y Monitoreo', {
            'fields': ('estado', 'error_message', 'ultima_comprobacion')
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en', 'creado_por'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dominio', 'creado_por')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'object_repr', 'ip_address')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'action', 'content_type', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent')
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_type', 'is_sensitive', 'description_short', 'updated_at', 'updated_by')
    list_filter = ('value_type', 'is_sensitive', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_sensitive:
            form.base_fields['value'].help_text = "Este campo contiene información sensible"
        return form

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

# Customize admin site
admin.site.site_header = "DMARC Panel Administration"
admin.site.site_title = "DMARC Panel Admin"
admin.site.index_title = "Welcome to DMARC Panel Administration"