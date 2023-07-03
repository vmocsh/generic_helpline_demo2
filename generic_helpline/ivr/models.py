from __future__ import unicode_literals

from django.db import models
from .options import Session
from management.models import HelpLine, HelperCategory
from registercall.models import Task
"""
   Model for storing incoming IVR calls
   session_next : It stores session for respective call object
   language_option : stores language selected by the user
   helpline_no : to identify between different helpine numbers
"""


class IVR_Call(models.Model):
    sid = models.CharField(max_length=256)
    caller_no = models.CharField(max_length=15)
    caller_location = models.CharField(max_length=256)
    helpline_no = models.CharField(max_length=15)
    language_option = models.CharField(max_length=20, default=None, null=True)
    category_option = models.CharField(max_length=20, default=None, null=True)
    category_sub_option = models.CharField(max_length=20, default=None, null=True)
    session_next = models.CharField(max_length=256, choices=Session.SESSION_CHOICES)

    def __str__(self):
        return str(self.caller_no)


"""
   Model for storing forward call request
   Object created at the time of call initiated through android app by helper and
   deleted after call ends
"""


class Call_Forward(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank='True', null=True)
    survey_task = models.ForeignKey("surveys.SurveyTask", on_delete=models.CASCADE, blank='True', null=True)
    helper_no = models.CharField(max_length=15)
    caller_no = models.CharField(max_length=15)
    type_options = (
        ('regular', 'regular'),
        ('survey', 'survey'),
    )
    type = models.CharField(max_length=13, choices=type_options, blank='True', null=True)


    def __str__(self):
        return str(self.helper_no)


"""
   Model for storing forward call request history for Call_Forward Model
   It also stores call status whether call was completed or was left unanswered
"""


class Call_Forward_Details(models.Model):
    status_choices = (
        ('initiated', 'initiated'),
        ('not_answered', 'not_answered'),
        ('completed', 'completed'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank='True', null=True)
    survey_task = models.ForeignKey("surveys.SurveyTask", on_delete=models.CASCADE, blank='True', null=True)
    helper_no = models.CharField(max_length=15)
    caller_no = models.CharField(max_length=15)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=15, choices=status_choices, default='initiated')
    call_duration = models.CharField(max_length=5, default='0')
    call_pickup_duration = models.CharField(max_length=5, default='0')
    call_recording = models.FileField(upload_to='recordings/', default='recordings/file.mp3')
    call_recording_name = models.CharField(max_length=30, null=True)
    type_options = (
        ('regular', 'regular'),
        ('survey', 'survey'),
    )
    type = models.CharField(max_length=13, choices=type_options, blank='True', null=True)

    def __str__(self):
        return str(self.helper_no)


"""
    Model for helpline languages
"""


class Language(models.Model):
    language = models.CharField(max_length=20)
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.language)


"""
IVR audios are associated to helpline categories (e.g. Arts, Science) and language (e.g. Hindi, English)
"""


class IVR_Audio(models.Model):
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    category = models.ForeignKey(HelperCategory, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    audio = models.FileField(upload_to='ivr_audio/')
    playorder = models.IntegerField(default=1)

    def __str__(self):
        return str(self.category)+" "+str(self.language)


"""
Misc categories includes Welcome, Terms, Exit & Language
"""


class Misc_Category(models.Model):
    category = models.CharField(max_length=20)

    def __str__(self):
        return str(self.category)


"""
Audio files for Misc Category values
"""


class Misc_Audio(models.Model):
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    category = models.ForeignKey(Misc_Category, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    audio = models.FileField(upload_to='ivr_audio/')
    playorder = models.IntegerField(default=1)

    def __str__(self):
        return str(self.category)+" "+str(self.language)

    # FEEDBACK SYSTEM ###


class FeedbackType(models.Model):
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    question = models.CharField(max_length=100)
    audio = models.FileField(upload_to='ivr_audio/')

    def __str__(self):
        return str(self.question)


class FeedbackResponse(models.Model):
    feedbackType = models.ForeignKey(FeedbackType, on_delete=models.CASCADE)
    response = models.IntegerField(default=2)

    def __str__(self):
        return str(self.id)


class Feedback(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    feedbackresponses = models.ManyToManyField(FeedbackResponse, blank=True, null=True)
    # current_question = models.ForeignKey(FeedbackResponse, on_delete=models.CASCADE)
    current_question = models.IntegerField(default=0)
    isCallRaised = models.BooleanField(default=False)
    isFeedbackTaken = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)
