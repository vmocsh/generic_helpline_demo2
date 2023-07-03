"""
Url config file for RegisterCall App
"""
from django.conf.urls import url

from task_manager.views import GetHelperTasks, GetTaskDetails

from .response_views import (FeedbackResponse, NewTaskResponse,
                             PrimaryResponse, SpecialistConfirmResponse,
                             SpecialistResponse)

urlpatterns = [
    url(r'^GetHelperTasks/$', GetHelperTasks.as_view(), name='get_helper_tasks'),
    url(r'^GetTaskDetails/$', GetTaskDetails.as_view(), name='get_task_details'),
    url(r'^NewTaskResponse/$', NewTaskResponse.as_view(), name='new_task_response'),
    url(r'^PrimaryResponse/$', PrimaryResponse.as_view(), name='primary_response'),
    url(r'^SpecialistResponse/$', SpecialistResponse.as_view(), name='specialist_response'),
    url(r'^FeedbackResponse/$', FeedbackResponse.as_view(), name='feedback_response'),
    url(r'^SpecialistConfirmResponse/$', SpecialistConfirmResponse.as_view(),
        name='specialist_confirm_response'),
]
