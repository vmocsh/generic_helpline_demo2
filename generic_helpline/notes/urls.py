from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from notes import views

urlpatterns = [
    path('api/notes/', views.NoteView.as_view()),
    path('api/notes/<int:pk>/', views.NoteView.as_view()),
    path('api/notes/me/', views.my_note),
    path('api/notes/others/', views.TaskNotesView.as_view()),
    path('api/attachments/', views.AttachmentList.as_view()),
    path('api/attachments/<int:pk>/', views.AttachmentDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
