from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class for super admin users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        )

class IsCompanyAdminOrSuperAdmin(permissions.BasePermission):
    """
    Permission class for company admins and super admins
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_super_admin or request.user.is_company_admin)
        )

class CanEditConfig(permissions.BasePermission):
    """
    Permission class for users who can edit configuration
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_edit_config
        )

class IsReadOnlyOrHigher(permissions.BasePermission):
    """
    Permission class for read-only users and above
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            not request.user.is_read_only or 
            request.method in permissions.SAFE_METHODS
        )

class HasCompanyAccess(permissions.BasePermission):
    """
    Permission class to check company access
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.is_super_admin:
            return True
        
        # Get the company from the object
        if hasattr(obj, 'empresa'):
            empresa_id = obj.empresa.id
        elif hasattr(obj, 'id') and hasattr(obj, 'usuarios'):  # This is a company object
            empresa_id = obj.id
        else:
            return False
        
        return user.has_company_access(empresa_id)