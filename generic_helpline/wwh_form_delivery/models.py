from django.db import models

from registercall.models import Task


class WhatsAppUser(models.Model):
    name = models.TextField(null=True)
    contact = models.IntegerField(primary_key=True)
    otp = models.TextField()
    location = models.TextField(null=True)
    is_updated = models.BooleanField(default=False)
    base32 = models.TextField()

class WhatsAppMessage(models.Model):
    message_id = models.AutoField(primary_key=True)
    text = models.TextField(blank=True)
    wwh_task_id = models.ForeignKey(Task, to_field='id', null=True, on_delete=models.CASCADE)  # wwh task_id
    sent = models.BooleanField(default=False, blank=True)  # message has been sent back to user or not
    language = models.TextField(null=True, blank=True)
    from_doctor = models.BooleanField(default=False)  # to differentiate between user and doctor messages
    attachment = models.ImageField(upload_to='attachments/', null=True, blank=True)
    contact = models.ForeignKey(WhatsAppUser, to_field='contact', null=True, on_delete=models.CASCADE)
    is_synced = models.BooleanField(default=True, blank=True)  # this message is synced with server
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    has_seen = models.BooleanField(default=False, blank=True)
