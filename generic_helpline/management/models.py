from __future__ import unicode_literals

from django.db import models
from .options import WeekDayOptions
from django.db.models import Aggregate, CharField, Value
import datetime

# Create your models here.


class HelpLine(models.Model):
    """
    Model for different helpline numbers
    Eg: General helping number, education specific etc.
    """
    name = models.CharField(max_length=64, default="General")
    helpline_number = models.CharField(max_length=16, unique=True)
    helpline_tollfree_number = models.CharField(max_length=16, unique=True, default=None)

    def __str__(self):
        return self.name


class HelperCategory(models.Model):
    """
    Model to map helpers to different categories, many-to-many from helpers side
    """
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class HelplineSetting(models.Model):
    """
    Model to store helpline specific settings
    """
    # Associated to helpline
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)

    # time in days
    reminder_time = models.IntegerField(default=1)
    # Time in days
    reassignment_time = models.IntegerField(default=3)

    def __str__(self):
        return self.helpline.name


class CategorySubcategory(models.Model):
    language_options = (
        ('english', 'en'),
        ('hindi', 'hi'),
        ('gujarati', 'gj'),
        ('marathi', 'mr')
    )
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    category = models.CharField(max_length=512)
    subcategory = models.CharField(max_length=512)
    language = models.CharField(max_length=13, choices=language_options, default='english')

    def __str__(self):
        return self.category+":"+self.subcategory


class AvailableSlot(models.Model):
    helper = models.ForeignKey('register_helper.Helper', on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=WeekDayOptions.DAY_CHOICES, default=None)
    start_time = models.TimeField('StartTimeStamp')
    end_time = models.TimeField('EndTimeStamp')
    is_available = models.BooleanField(default=True)

class DoctorAvailableSlot(models.Model):
    # slot_id = models.AutoField(primary_key=True)
    doctor_id = models.IntegerField('DoctorID', default=0)
    doctor_name = models.CharField(max_length=512, default="")
    slot_date = models.DateField('Date', default='2022-02-12')
    slot_start_times = models.CharField(max_length=1024, default="")

class DoctorBookedSlot(models.Model):
    task_id = models.ForeignKey('registercall.Task', on_delete=models.CASCADE)
    helper = models.ForeignKey('register_helper.Helper', on_delete=models.CASCADE)
    doctor_name = models.CharField(max_length=512)
    slot_date = models.DateField('Date')
    slot_time = models.CharField(max_length=1024)






class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(expressions)s)'

    def __init__(self, expression, delimiter, **extra):
        output_field = extra.pop('output_field', CharField())
        delimiter = Value(delimiter)
        super(GroupConcat, self).__init__(
            expression, delimiter, output_field=output_field, **extra)

    def as_sqlite(self, compiler, connection, **extra_context):
        return super(GroupConcat, self).as_sqlite(compiler, connection)

    def as_sql(self, compiler, connection, **extra_context):
        return super(GroupConcat, self).as_sql(compiler, connection)

class Tag_List(models.Model):
    tag = models.CharField(max_length=90)


