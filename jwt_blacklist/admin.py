from django.contrib import admin
from .models import OutstandingToken, BlacklistedToken

@admin.register(OutstandingToken)
class OutstandingTokenAdmin(admin.ModelAdmin):
    list_display = ('jti', 'user', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'jti')
    readonly_fields = ('jti', 'token', 'created_at', 'expires_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'blacklisted_at')
    list_filter = ('blacklisted_at',)
    search_fields = ('token__user__email', 'token__jti')
    readonly_fields = ('token', 'blacklisted_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
