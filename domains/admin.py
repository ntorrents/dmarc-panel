from django.contrib import admin
from .models import Domain, DNSRecord

# Register your models here.

admin.site.register(Domain)
admin.site.register(DNSRecord)

