from django.conf.urls import url

from .views import (Helplines, HelperProfile, getHelperCategoryandSubcategory, Languages, AllClients,
                    HelplineCategories, HelperTasks, ClientTasks,
                    setHelperCategoryandLanguage, HelperAccept, HelplineNumber, QandADetails, TaskComplete, SurveyTaskComplete, CallForward,
                    ActivateHelper, Refresh_GCM,
                    HelperFeedbackTasks, HelperFeedbackReply, DeleteActivation, ActivateAllHelper,
                    DeactivateAllHelper, AllHelpers, ReallocateTask, HelperAcceptReallocate, SendSms, TagUpdate,SurveyTagUpdate , NameUpdate, FormEditUrl, TagFields,
                    CreateFollowUpTask, CreateSurveyFollowUpTask, AvailableSlots, DoctorAvailableSlots, DoctorBookedSlots, newClientTasks)

urlpatterns = [
    url(r'^helplines/$', Helplines.as_view(), name='Helplines'),
    url(r'^HelplineNumber/$', HelplineNumber.as_view(), name='HelplineNumber'),
    url(r'^AllHelpers/$', AllHelpers.as_view(), name='AllHelpers'),
    url(r'^Languages/$', Languages.as_view(), name='Languages'),
    url(r'^AllClients/$', AllClients.as_view(), name='AllClients'),
    url(r'^getHelperCategoryandSubcategory/$', getHelperCategoryandSubcategory.as_view(), name='getHelperCategoryandSubcategory'),
    url(r'^HelperProfile/$', HelperProfile.as_view(), name='HelperProfile'),
    url(r'^setHelperCategoryandLanguage/$', setHelperCategoryandLanguage.as_view(), name='setHelperCategoryandLanguage'),
    url(r'^HelplineCategories/$', HelplineCategories.as_view(), name='HelplineCategories'),
    url(r'^HelperTasks/$', HelperTasks.as_view(), name='HelperTasks'),
    url(r'^HelperFeedbackTasks/$', HelperFeedbackTasks.as_view(), name='HelperFeedbackTasks'),
    url(r'^HelperFeedbackReply/$', HelperFeedbackReply.as_view(), name='HelperFeedbackReply'),
    url(r'^HelperAccept/$', HelperAccept.as_view(), name='HelperAccept'),
    url(r'^HelperAcceptReallocate/$', HelperAcceptReallocate.as_view(), name='HelperAcceptReallocate'),
    url(r'^ReallocateTask/$', ReallocateTask.as_view(), name='ReallocateTask'),
    url(r'^QandADetails/$', QandADetails.as_view(), name='QandADetails'),
    url(r'^TaskComplete/$', TaskComplete.as_view(), name='TaskComplete'),
    url(r'^SurveyTaskComplete/$', SurveyTaskComplete.as_view(), name='SurveyTaskComplete'),
    url(r'^ClientTasks/$', ClientTasks.as_view(), name='ClientTasks'),
    url(r'^CallForward/$', CallForward.as_view(), name='CallForward'),
    url(r'^RefreshGcm/$', Refresh_GCM.as_view(), name='RefreshGcm'),
    url(r'^activateHelper/(?P<id>[0-9]+)/$', ActivateHelper.as_view(), name='ActivateHelper'),
    url(r'^activateAllHelper/$', ActivateAllHelper.as_view(), name='ActivateAllHelper'),
    url(r'^deactivateHelper/(?P<id>[0-9]+)/$', DeleteActivation.as_view(), name='DeactivateHelper'),
    url(r'^deactivateAllHelper/$', DeactivateAllHelper.as_view(), name='DeactivateAllHelper'),
    url(r'^SendSms/$', SendSms.as_view(), name='SendSms'),
    url(r'^TagUpdate/$', TagUpdate.as_view(), name='TagUpdate'),
    url(r'^SurveyTagUpdate/$', SurveyTagUpdate.as_view(), name='SurveyTagUpdate'),
    url(r'^NameUpdate/$', NameUpdate.as_view(), name='NameUpdate'),
    url(r'^CreateFollowUpTask/$', CreateFollowUpTask.as_view(), name='CreateFollowUpTask'),
    url(r'^CreateSurveyFollowUpTask/$', CreateSurveyFollowUpTask.as_view(), name='CreateSurveyFollowUpTask'),
    url(r'^AvailableSlots/$', AvailableSlots.as_view(), name='AvailableSlots'),
    url(r'^DoctorAvailableSlots/$', DoctorAvailableSlots.as_view(), name='DoctorAvailableSlots'),
    url(r'^DoctorBookedSlots/$', DoctorBookedSlots.as_view(), name='DoctorBookedSlots'),
    url(r'^FormEditUrl/$', FormEditUrl.as_view(), name='FormEditUrl'),
    url(r'^TagFields/$', TagFields.as_view(), name='TagFields'),
    url(r'^getClientTasks/$', newClientTasks.as_view(), name='getClientTasks'),
]