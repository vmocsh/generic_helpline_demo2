from django.contrib import admin
from .models import HelpLine, HelperCategory, HelplineSetting, CategorySubcategory, AvailableSlot, Tag_List
# Register your models here.
admin.site.register(HelpLine)
admin.site.register(HelperCategory)


class HelplineSetting_Admin(admin.ModelAdmin):
    list_display = ["helpline", "reminder_time", "reassignment_time"]

    class Meta:
        model = HelplineSetting


class CategorySubcategory_Admin(admin.ModelAdmin):
    list_display = ["helpline", "category", "subcategory"]

    class Meta:
        model = CategorySubcategory


class AvailableSlot_Admin(admin.ModelAdmin):
    list_display = ['helper', 'day_of_week', 'start_time', 'end_time', 'is_available']

    class Meta:
        model = AvailableSlot

class TagList_Admin(admin.ModelAdmin):
    list_display = ['tag']

    class Meta:
        model = Tag_List


admin.site.register(CategorySubcategory, CategorySubcategory_Admin)
admin.site.register(HelplineSetting, HelplineSetting_Admin)
admin.site.register(AvailableSlot, AvailableSlot_Admin)
admin.site.register(Tag_List, TagList_Admin)





