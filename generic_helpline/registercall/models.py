"""
Register Call Models
"""
from django.db import models

from management.models import HelpLine, HelperCategory, CategorySubcategory
from register_client.models import Client

from registercall.options import (CallRequestStatusOptions,
                                  TaskStatusOptions, TaskType)


class CallRequest(models.Model):
    """
    Model for storing incoming call requests
        Calls for whom task is already pending is merged
        Calls for whom client is blocked is blocked
        If above two condition fails is when task is created

    Refers to helpline and client
    """

    helpline = models.ForeignKey(HelpLine, related_name='call_requests', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='call_requests', on_delete=models.CASCADE)

    created = models.DateTimeField('Created Timestamp', auto_now_add=True)

    status = models.IntegerField(
        default=CallRequestStatusOptions.CREATED,
        choices=CallRequestStatusOptions.STATUS_CHOICES,
    )

    def __str__(self):
        return str(self.pk)


class Task(models.Model):
    """
    Model for the actual Tasks created
    Creates only when request is valid and task not already pending

    Refers to call request
    """
    # Each helper may belong to more than one category
    call_request = models.ForeignKey(CallRequest, related_name='tasks', on_delete=models.CASCADE)
    category = models.ForeignKey(
        HelperCategory,
        related_name='tasks',
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    taskcategory = models.ManyToManyField(CategorySubcategory, related_name='taskcategory', default=None, blank=True)

    tasksubcategory = models.ManyToManyField(CategorySubcategory, related_name='tasksubcategory', default=None,
                                             blank=True)

    language = models.ManyToManyField('ivr.Language', blank=True)
    created = models.DateTimeField('Created Timestamp', auto_now_add=True)
    modified = models.DateTimeField('Modified Timestamp', auto_now=True)
    tag_string = models.CharField(max_length=256, default="", null=True, blank=True)
    task_type = models.IntegerField(
        default=TaskType.INDIRECT,
        choices=TaskType.TYPE_CHOICES
    )
    status = models.IntegerField(
        default=TaskStatusOptions.PENDING,
        choices=TaskStatusOptions.STATUS_CHOICES,
    )
    call_attempt = models.IntegerField(default=0)
    client_calls = models.IntegerField(default=1)
    from_whatsapp = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return str(self.pk)


class FollowUpTask(models.Model):
    active_options = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    )

    parent_task = models.ForeignKey(Task, related_name='p_task', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='f_task', null=True, on_delete=models.CASCADE)
    helper = models.ForeignKey('register_helper.Helper', related_name='follow_to', blank=True, null=True,
                               on_delete=models.CASCADE)
    marked_date = models.DateTimeField('Marked Timestamp')
    created_date = models.DateField('Created Timestamp')
    status = models.IntegerField(
        default=TaskStatusOptions.PENDING,
        choices=TaskStatusOptions.STATUS_CHOICES,
    )
    create_status = models.CharField(max_length=13, choices=active_options, default='Inactive')

    def __str__(self):
        return str(self.pk)
