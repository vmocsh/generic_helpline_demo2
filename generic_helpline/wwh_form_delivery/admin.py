from django.contrib import admin

from .models import WhatsAppUser, WhatsAppMessage

admin.site.register(WhatsAppUser)
admin.site.register(WhatsAppMessage)
