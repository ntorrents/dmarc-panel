from django.db import models
from django.conf import settings

class Domain(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_company = models.CharField(max_length=255, blank=True, null=True)
    compliance_level = models.CharField(max_length=50, blank=True, null=True)  # para filtrado posterior
    tag = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class DNSRecord(models.Model):
    DNS_TYPE_CHOICES = [
        ('SPF', 'SPF'),
        ('DKIM', 'DKIM'),
        ('DMARC', 'DMARC'),
    ]

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='dns_records')
    type = models.CharField(max_length=10, choices=DNS_TYPE_CHOICES)
    value = models.TextField()
    status = models.CharField(max_length=50, default='pending')  # valid, invalid, error, etc.
    last_checked = models.DateTimeField(auto_now=True)
    selector = models.CharField(max_length=100, blank=True, null=True)  # solo para DKIM
    policy = models.CharField(max_length=10, blank=True, null=True)     # solo para DMARC

    def __str__(self):
        return f"{self.domain.name} - {self.type}"
