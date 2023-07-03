from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from notes.models import Note, Attachment
from notes.serializers import NoteSerializer, AttachmentSerializer
from register_helper.models import Helper
from django.db.models import Q


class TaskNotesView(generics.ListAPIView):
    serializer_class = NoteSerializer

    def get_queryset(self):
        username = self.request.query_params.get('username')
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        queryset = Note.objects.none()
        print(self.request.query_params.get('origin'))
        if "Call" == (self.request.query_params.get('origin')):
            queryset = Note.objects.filter(task_id=self.request.query_params.get('task_id')).exclude(
            helper_id=helper.id).exclude(Q(attachment__isnull=True) & Q(text__isnull=True))
       
        if "System" == (self.request.query_params.get('origin')):
            queryset = Note.objects.filter(survey_task_id=self.request.query_params.get('survey_task_id')).exclude(
            helper_id=helper.id).exclude(Q(attachment__isnull=True) & Q(text__isnull=True))

        if "Followup" == (self.request.query_params.get('origin')):
            queryset = Note.objects.filter(task_id=self.request.query_params.get('task_id')).exclude(
            helper_id=helper.id).exclude(Q(attachment__isnull=True) & Q(text__isnull=True)
            ) | Note.objects.filter(task_id=self.request.query_params.get('parent_task')).exclude(Q(attachment__isnull=True) & Q(text__isnull=True))

        if "survey_followup" == (self.request.query_params.get('origin')):
            queryset = Note.objects.filter(survey_task_id=self.request.query_params.get('survey_task_id')).exclude(
            helper_id=helper.id).exclude(Q(attachment__isnull=True) & Q(text__isnull=True)
            ) | Note.objects.filter(survey_task_id=self.request.query_params.get('parent_task')).exclude(Q(attachment__isnull=True) & Q(text__isnull=True))

        return queryset


@api_view(['POST'])
def my_note(request):
    user = get_object_or_404(User, username=request.data['username'])
    helper = Helper.objects.filter(user=user).first()
    taskId = request.data['task_id']
    surveyId = request.data['survey_task_id']
    note = Note.objects.none()
    if (surveyId is None) or (surveyId == '0'):
        note = Note.objects.filter(helper=helper, task_id=request.data['task_id']).last()
        if not note:
            note = Note(task_id=request.data['task_id'], helper=helper, helper_name=helper.user.get_full_name())
            note.save()

    if (taskId is None) or (taskId == '0'):
        note = Note.objects.filter(helper=helper, survey_task_id=request.data['survey_task_id']).last()
        if not note:
            note = Note(survey_task_id=request.data['survey_task_id'], helper=helper, helper_name=helper.user.get_full_name())
            note.save()

    print("debug")
    print(taskId)
    print(surveyId)
    print(note)

    serializer = NoteSerializer(note)
    return Response(serializer.data)


class NoteView(APIView):
    """
        Retrieve, update or delete a snippet instance.
        """

    def get_object(self, pk):
        try:
            return Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        note = self.get_object(pk)
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def post(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        helper = Helper.objects.filter(user=user).first()
        survey_task_id = request.data['survey_task_id']
        note = Note(task_id=request.data['task_id'], helper=helper)
        if not (survey_task_id == '0' or survey_task_id is None):
            note = Note(survey_task_id=request.data['survey_task_id'], helper=helper)
        if 'text' in request.data:
            note.text = request.data['text']
        note.helper_name = note.helper.user.get_full_name()
        note.save()
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def put(self, request, pk):
        note = self.get_object(pk)
        note.text = request.data['text']
        note.save()
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def delete(self, request, pk):
        note = self.get_object(pk)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttachmentList(generics.ListCreateAPIView):
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return Attachment.objects.filter(note_id=self.request.query_params.get('note_id'))


class AttachmentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
