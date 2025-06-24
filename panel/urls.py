from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DominioViewSet, DNSRecordViewSet, ClienteViewSet, TagViewSet,
    DominioUsuarioAccesoViewSet, AuditLogViewSet, SystemSettingViewSet
)

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'dominios', DominioViewSet, basename='dominio')
router.register(r'dns-records', DNSRecordViewSet, basename='dnsrecord')
router.register(r'domain-access', DominioUsuarioAccesoViewSet, basename='dominiousuarioacceso')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'system-settings', SystemSettingViewSet, basename='systemsetting')

urlpatterns = [
    path('', include(router.urls)),
]