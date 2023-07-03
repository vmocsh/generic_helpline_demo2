from django.contrib import admin
from .models import Client
# Register your models here.

class ClientAdmin(admin.ModelAdmin):
    list_display = ['client_number','name','location','lastSMSSent']
    class Meta:
        model = Client

admin.site.register(Client,ClientAdmin)
