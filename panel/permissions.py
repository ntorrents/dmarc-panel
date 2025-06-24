from rest_framework import permissions
from .models import DominioUsuarioAcceso

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user

class CanManageDomain(permissions.BasePermission):
    """
    Custom permission to check if user can manage a domain.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superusers and admin role users can access everything
        if user.is_superuser or user.rol == 'admin':
            return True
        
        # Get the domain object
        if hasattr(obj, 'dominio'):
            domain = obj.dominio
        elif hasattr(obj, 'nombre'):  # This is a domain object
            domain = obj
        else:
            return False
        
        # Check if user has access to this domain
        try:
            access = DominioUsuarioAcceso.objects.get(user=user, dominio=domain)
            
            # For read operations, any access level is sufficient
            if request.method in permissions.SAFE_METHODS:
                return True
            
            # For write operations, need admin or editor role
            return access.rol in ['admin', 'editor']
            
        except DominioUsuarioAcceso.DoesNotExist:
            return False

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or request.user.rol == 'admin'
        )