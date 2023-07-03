"""
Admin view management for register call
"""
from django.contrib import admin

from .models import  Helper, HelperCategory


class HelperAdmin(admin.ModelAdmin):
    list_display = ["id", "user",  "get_categories", "get_languages", "helper_number", "level"]

    class Meta:
        model = Helper

admin.site.register(Helper, HelperAdmin)

