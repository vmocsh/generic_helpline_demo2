from __future__ import unicode_literals

from django.db import models
from register_client.models import Client
from register_helper.models import Helper
# Create your models here.


class Survey(models.Model):
    """
    Model for details of survey
    """
    name = models.CharField(max_length=128, null=True, default=None, blank=True)
    google_form_url = models.URLField(max_length=800, default=None)
    response_csv_url = models.URLField(max_length=800, default=None)
    initial_csv = models.FileField(upload_to='survey', null=True, default=None, blank=True)
    google_response_csv = models.FileField(upload_to='survey', null=True, default=None, blank=True)
    number_of_people = models.IntegerField(default=None)
    created = models.DateTimeField('Created Timestamp', auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "  Surveys"


class SurveyTask(models.Model):
    """
    Model for all survey tasks
    """
    status_options = (
        ('pending', 'pending'),
        ('assigned', 'assigned'),
        ('completed', 'completed'),
        ('fo_assigned', 'fo_assigned'),
        ('fo_completed', 'fo_completed')
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    edit_form_url = models.URLField(max_length=800, null=True,blank=True, default=None)
    helper = models.ForeignKey(Helper, null=True, default=None, on_delete=models.CASCADE)
    status = models.CharField(max_length=13, choices=status_options, default='pending')
    tag_string = models.CharField(max_length=256, default="", null=True, blank=True)
    assignedDateTime = models.DateTimeField("Assigned on", blank=True, null=True)
    completedDateTime = models.DateTimeField("Completed on", blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = " Survey tasks"

class FollowUpSurveyTask(models.Model):
    active_options = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    )
    status_options = (
        ('pending', 'pending'),
        ('assigned', 'assigned'),
        ('completed', 'completed')
    )

    parent_task = models.ForeignKey(SurveyTask, related_name='p_task', on_delete=models.CASCADE)
    task = models.ForeignKey(SurveyTask, related_name='f_task', null=True, on_delete=models.CASCADE)
    helper = models.ForeignKey(Helper, related_name='follow_to_helper', blank=True, null=True,
                               on_delete=models.CASCADE)
    marked_date = models.DateTimeField('Marked Timestamp')
    created_date = models.DateField('Created Timestamp')
    status = models.CharField(max_length=13, choices=status_options, default='pending')
    create_status = models.CharField(max_length=13, choices=active_options, default='Inactive')

    def __str__(self):
        return str(self.pk)


class SurveyResponse(models.Model):
    """
    Model for storing survey data
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    survey_task = models.ForeignKey(SurveyTask, on_delete=models.CASCADE)
    survey_data = models.CharField(max_length=10000, blank=True)
    modified = models.DateTimeField('Modified Timestamp', auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name_plural = "Survey responses"
