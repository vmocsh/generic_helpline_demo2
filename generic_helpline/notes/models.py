from django.db import models

from register_client.models import Client
from register_helper.models import Helper
from registercall.models import Task


# Create your models here.
class Note(models.Model):
    note_id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank='True', null=True)
    survey_task = models.ForeignKey("surveys.SurveyTask", on_delete=models.CASCADE, blank='True', null=True)
    helper = models.ForeignKey(Helper, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    helper_name = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)


class Attachment(models.Model):
    image = models.FileField(upload_to='notes', blank=True)
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
