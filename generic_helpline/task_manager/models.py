"""
Models related to task management
"""

from django.db import models

from register_helper.models import Helper
from registercall.models import Task
from .options import (ActionStatusOptions, ActionTypeOptions,
                      AssignStatusOptions)


class Action(models.Model):
    """
    Model for actions for a specific task
    Refers to task
    """
    task = models.ForeignKey(Task, related_name='actions', on_delete=models.CASCADE)

    created = models.DateTimeField('Created Timestamp', auto_now_add=True)
    modified = models.DateTimeField('Modified Timestamp', auto_now=True)

    action_type = models.IntegerField(
        default=ActionTypeOptions.PRIMARY,
        choices=ActionTypeOptions.ACTION_CHOICES,
    )
    status = models.IntegerField(
        default=ActionStatusOptions.ASSIGN_PENDING,
        choices=ActionStatusOptions.STATUS_CHOICES,
    )

    def __str__(self):
        return str(self.pk)


class Assign(models.Model):
    """
    Model for helpers assigned to a particular action
    Refers to action and helper
    """
    helper = models.ForeignKey(Helper, related_name='assigned_to', on_delete=models.CASCADE)
    action = models.ForeignKey(Action, related_name='assigned_to', on_delete=models.CASCADE)

    created = models.DateTimeField('Created Timestamp', auto_now_add=True)
    accepted = models.DateTimeField('Accepted Timestamp', null=True)
    modified = models.DateTimeField('Modified Timestamp', auto_now=True)

    status = models.IntegerField(
        default=AssignStatusOptions.PENDING,
        choices=AssignStatusOptions.STATUS_CHOICES,
    )

    def get_taskid(self):
        return self.action.task.id

    def __str__(self):
        return str(self.pk)


class QandA(models.Model):
    """
    Model for storing the questions and answers for every task
    Refers to task
    """
    task = models.ForeignKey(Task, related_name='q_and_a', on_delete=models.CASCADE)
    created = models.DateTimeField('Created Timestamp', auto_now_add=True)

    # Question obtained from primary and updated by specialist helper, Answer from specialist
    question = models.CharField(max_length=512, null=True, default=None, blank=True)
    answer = models.CharField(max_length=512, null=True, default=None, blank=True)
    message = models.CharField(max_length=512, null=True, default=None, blank=True)

    rating = models.FloatField(default=0.0)


class Feedback(models.Model):
    status_options = (
        ('pending', 'pending'),
        ('completed', 'completed')
    )
    q_a = models.ForeignKey(QandA, related_name='q_and_a', on_delete=models.CASCADE)
    helper = models.ForeignKey(Helper, related_name='helper', on_delete=models.CASCADE)
    rating = models.FloatField(default=0.0)
    status = models.CharField(max_length=13, choices=status_options, default='pending')
    comment = models.CharField(max_length=512, default=None, null=True)

    def __str__(self):
        return str(self.q_a)


class TaskHistory(models.Model):
    task = models.ForeignKey(Task, related_name='taskhist', on_delete=models.CASCADE)
    fromHelper = models.ForeignKey(Helper, related_name='fromhelper', blank=True, on_delete=models.CASCADE)
    toHelper = models.ForeignKey(Helper, related_name='tohelper', blank=True, on_delete=models.CASCADE)
    reason = models.CharField(max_length=512, default=None, null=True)
    reallocateDate = models.DateTimeField('Reallocated Timestamp', auto_now_add=True)

    def __str__(self):
        return str(self.task)