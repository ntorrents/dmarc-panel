from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()

class OutstandingToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    jti = models.CharField(unique=True, max_length=255)
    token = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ("user",)
        verbose_name = _("Outstanding token")
        verbose_name_plural = _("Outstanding tokens")

    def __str__(self):
        return "Token for {} ({})".format(
            self.user,
            self.jti,
        )

class BlacklistedToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.OneToOneField(OutstandingToken, on_delete=models.CASCADE)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Blacklisted token")
        verbose_name_plural = _("Blacklisted tokens")

    def __str__(self):
        return f"Blacklisted token for {self.token.user}"
