from django.conf.urls import url
from .views import Home,Helper_Profile,Yearly_Stats,Task_Details,Update_Survey_Users,Survey_Users,Monthly_Stats,BulkHelperRegistration,DeleteHelper,QandA_Category, view_surveys, combined_csv, Create_Survey, Create_Tasks, Clientwise_Surveys, Client_Profile, download_csv, tag_list, DoctorSlots, AddTaskDashboard 

urlpatterns = [
url(r'^$', Home.as_view(), name='home'),
url(r'^helper_profile/(?P<pk>[0-9]+)/(?P<cat>[a-zA-Z]+)/(?P<year>[0-9]{4})/', Helper_Profile.as_view(), name='helper_profile'),
url(r'^yearly_stats/(?P<cat>[a-zA-Z0-9 -]+)/(?P<year>[0-9]{4})/', Yearly_Stats.as_view(), name='yearly_stats'),
url(r'^monthly_stats/(?P<cat>[a-zA-Z0-9 -]+)/(?P<month>[a-zA-Z]+)/(?P<year>[0-9]{4})/', Monthly_Stats.as_view(), name='monthly_stats'),
url(r'^task_details/(?P<pk>[0-9]+)/', Task_Details.as_view(), name='task_details'),
url(r'^survey_details/(?P<pk>[0-9]+)/', Survey_Users.as_view(), name='survey_details'),
url(r'^update_survey_users/(?P<pk>[0-9]+)/', Update_Survey_Users.as_view(), name='update_survey_users'),
url(r'^bulk_registration/', BulkHelperRegistration.as_view(), name='bulk_registration'),
url(r'^update_doctor_slot/', DoctorSlots.as_view(), name='update_doctor_slot'),
url(r'^create_survey/', Create_Survey.as_view(), name='create_survey'),
url(r'^create_tasks/', Create_Tasks.as_view(), name='create_tasks'),
url(r'^delete_helper/(?P<pk>[0-9]+)/', DeleteHelper.as_view(), name='delete_helper'),
url(r'^list_qanda/(?P<cat>[a-zA-Z]+)/', QandA_Category.as_view(), name='list_qanda'),
url(r'^view_surveys/', view_surveys.as_view(), name='view_surveys'),
url(r'^combined_csv/', combined_csv.as_view(), name='combined_csv'),
url(r'^download_csv/(?P<pk>[0-9]+)/', download_csv.as_view(), name='download_csv'),
url(r'^clientwise_surveys/', Clientwise_Surveys.as_view(), name='clientwise_surveys'),
url(r'^client_profile/(?P<pk>[0-9]+)/', Client_Profile.as_view(), name='client_profile'),
url(r'^tag_list/', tag_list.as_view(), name='tag_list'),
url(r'^add_task/',
        AddTaskDashboard, name='add_task'),
]