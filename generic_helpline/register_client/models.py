from __future__ import unicode_literals

from django.db import models
from .options import ClientStatusOptions

# Create your models here.


class Client(models.Model):
    """
    Model for details of people who are seeking for help
    New client gets added every time a request from new number is incoming
    """
    name = models.CharField(max_length=128, null=True, default=None, blank=True)
    location = models.CharField(max_length=128, null=True, default=None, blank=True)
    client_number = models.CharField(max_length=16, unique=True)
    lastSMSSent = models.DateTimeField('Last SMS Timestamp', auto_now=True, null=True)

    status = models.IntegerField(
        default=ClientStatusOptions.ACTIVE,
        choices=ClientStatusOptions.STATUS_CHOICES,
    )

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.client_number

    def is_blocked(self):
        """
        To check if client is blocked
        """
        return self.status == ClientStatusOptions.BLOCKED
