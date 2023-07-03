from django.contrib import admin
from .models import IVR_Call,Call_Forward,Language,IVR_Audio,Misc_Audio,Misc_Category,Feedback,FeedbackType,FeedbackResponse,Call_Forward_Details

# Register your models here.

class IVR_Admin(admin.ModelAdmin):
    list_display = ["caller_no","caller_location"]
    class Meta:
        model= IVR_Call

class FeedbackType_Admin(admin.ModelAdmin):
    list_display = ["id","helpline","question","audio"]
    class Meta:
        model= FeedbackType

class Call_Details_Admin(admin.ModelAdmin):
    list_display = ["type", "task","survey_task","helper_no","caller_no","created","updated","status","call_duration"]
    class Meta:
        model= Call_Forward_Details

class Call_Forward_Admin(admin.ModelAdmin):
    list_display = ["type", "task","survey_task","helper_no","caller_no"]
    class Meta:
        model= Call_Forward

admin.site.register(IVR_Call,IVR_Admin)
admin.site.register(Call_Forward, Call_Forward_Admin)
admin.site.register(Call_Forward_Details, Call_Details_Admin)
admin.site.register(Language)
admin.site.register(IVR_Audio)
admin.site.register(Misc_Audio)
admin.site.register(Misc_Category)
admin.site.register(Feedback)
admin.site.register(FeedbackType, FeedbackType_Admin)
admin.site.register(FeedbackResponse)
