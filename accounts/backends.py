# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        print(f"📢 EmailBackend activado - Email recibido: {email}")
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            print("❌ Usuario no encontrado")
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            print("✅ Usuario autenticado")
            return user

        print("❌ Contraseña inválida o usuario inactivo")
        return None

