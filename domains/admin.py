from django.contrib import admin
from .models import Domain, SPFRecord, DKIMKey, DMARCRecord

# Register your models here.

admin.site.register(Domain)
admin.site.register(SPFRecord)
admin.site.register(DKIMKey)
admin.site.register(DMARCRecord)
