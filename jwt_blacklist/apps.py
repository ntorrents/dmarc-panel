from django.apps import AppConfig


class JwtBlacklistConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jwt_blacklist'
    verbose_name = 'JWT Token Blacklist'
