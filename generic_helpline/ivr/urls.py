from django.conf.urls import url

from .views import IVR, FeedbackView


urlpatterns = [
    url(r'^feedback/$', FeedbackView.as_view(), name='getFeedback'),
    url(r'^$', IVR.as_view(), name='getIVR'),
]
