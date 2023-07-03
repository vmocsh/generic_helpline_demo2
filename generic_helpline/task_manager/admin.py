"""
Admin view management for task manager app
"""
from django.contrib import admin

from .models import Action, Assign, QandA, Feedback, TaskHistory


class QandAAdmin(admin.ModelAdmin):
    list_display = ["task", "created", "question", "answer", "rating"]

    class Meta:
        model = QandA


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["q_a", "helper", "rating", "status"]

    class Meta:
        model = Feedback


class AssignAdmin(admin.ModelAdmin):
    list_display = ["id", "get_taskid", "action", "helper", "status", "created", "accepted", "modified"]

    class Meta:
        model = Assign

class ActionAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "action_type", "status"]
    class Meta:
        model = Action

class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "fromHelper", "toHelper", "reason", "reallocateDate"]
    class Meta:
        model = TaskHistory

admin.site.register(Action, ActionAdmin)
admin.site.register(Assign, AssignAdmin)
admin.site.register(QandA,QandAAdmin)
admin.site.register(Feedback,FeedbackAdmin)
admin.site.register(TaskHistory, TaskHistoryAdmin)
