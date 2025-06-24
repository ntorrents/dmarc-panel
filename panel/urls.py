from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import DominioViewSet, DNSRecordViewSet, ClienteViewSet

router = DefaultRouter()
router.register(r'dominios', DominioViewSet)
router.register(r'records', DNSRecordViewSet)
router.register(r'clientes', ClienteViewSet) 

urlpatterns = [
    path('', include(router.urls)),  # Esto añade /dominios/ y /records/
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
