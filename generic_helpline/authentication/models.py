from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Forgot_Password(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


