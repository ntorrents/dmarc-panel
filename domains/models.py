from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Domain(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SPFRecord(models.Model):
    domain = models.OneToOneField(Domain, on_delete=models.CASCADE)
    record_text = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

class DKIMKey(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    selector = models.CharField(max_length=100)
    public_key = models.TextField()
    private_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DMARCRecord(models.Model):
    domain = models.OneToOneField(Domain, on_delete=models.CASCADE)
    policy = models.CharField(max_length=10)
    rua = models.TextField()
    ruf = models.TextField(blank=True, null=True)
    pct = models.IntegerField(default=100)
    record_text = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)