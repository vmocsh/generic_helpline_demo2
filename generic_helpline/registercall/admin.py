"""
Admin view management for register call
"""
from django.contrib import admin

from .models import CallRequest, Task, FollowUpTask


class AdminRegisterCall(admin.ModelAdmin):
    list_display = ['id','helpline', 'client', 'created', 'status']

    class Meta:
        model = CallRequest


class AdminTask(admin.ModelAdmin):
    list_display = ['id', 'request_call_id', 'helpline', 'category', 'created', 'modified', 'status', 'tag_string']

    class Meta:
        model = Task

    def request_call_id(self, obj):
        return obj.call_request

    def helpline(self, obj):
        return obj.call_request.helpline.name


class AdminFollowUpTask(admin.ModelAdmin):
    list_display = ['id', 'parent_task', 'created_date', 'marked_date', 'status']

    class Meta:
        model = FollowUpTask


admin.site.register(CallRequest, AdminRegisterCall)
admin.site.register(Task, AdminTask)
admin.site.register(FollowUpTask, AdminFollowUpTask)
