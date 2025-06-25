from django.urls import path
from .views import RegisterView, LoginView, MeView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),   # POST /api/auth/register/
    path('login/', LoginView.as_view(), name='login'),            # POST /api/auth/login/
    path('logout/', LogoutView.as_view(), name='logout'),         # POST /api/auth/logout/
    path('me/', MeView.as_view()),                                # GET /api/auth/me/
]

