from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthView, RegisterView, ProfileView, 
    EmpresaViewSet, RoleViewSet, UserViewSet
)

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/', AuthView.as_view(), name='auth'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', include(router.urls)),
]