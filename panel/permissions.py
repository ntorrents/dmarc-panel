from rest_framework import permissions
from accounts.permissions import HasCompanyAccess

class CanManageDomain(permissions.BasePermission):
    """
    Custom permission to check if user can manage a domain.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Super admins can access everything
        if user.is_super_admin:
            return True
        
        # Get the domain object
        if hasattr(obj, 'dominio'):
            domain = obj.dominio
        elif hasattr(obj, 'empresa'):  # This is a domain object
            domain = obj
        else:
            return False
        
        # Check company access
        if not user.has_company_access(domain.empresa.id):
            return False
        
        # For read operations, any authenticated user with company access can read
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, need config permissions or higher
        return user.can_edit_config

class CanManageCompanyData(permissions.BasePermission):
    """
    Permission to manage data within user's company
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

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
        
        # Check company access
        if not user.has_company_access(empresa_id):
            return False
        
        # For read operations
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, need config permissions or higher
        return user.can_edit_config

class IsReadOnlyOrCanEdit(permissions.BasePermission):
    """
    Permission that allows read-only users to read, but requires edit permissions for write operations
    """
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return user.can_edit_config