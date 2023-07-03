from django.contrib import admin
from .models import Survey, SurveyTask,  SurveyResponse ,FollowUpSurveyTask
# Register your models here.

class SurveyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'google_form_url', 'response_csv_url', 'number_of_people', 'created']
    class Meta:
        model = Survey

class SurveyTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'survey', 'client', 'helper', 'status', 'assignedDateTime', 'completedDateTime', 'edit_form_url']
    class Meta:
        model = SurveyTask

class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'survey', 'modified', 'survey_task', 'survey_data']
    class Meta:
        model = SurveyResponse

class FollowUpSurveyTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'parent_task', 'created_date', 'marked_date', 'status']
    class Meta:
        model = FollowUpSurveyTask


admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyTask, SurveyTaskAdmin)
admin.site.register(SurveyResponse, SurveyResponseAdmin)
admin.site.register(FollowUpSurveyTask, FollowUpSurveyTaskAdmin)