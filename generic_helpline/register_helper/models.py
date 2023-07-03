from django.contrib.auth.models import User
from django.db import models

from ivr.models import Language
from management.models import HelperCategory, HelpLine, CategorySubcategory
from .options import HelperStatusOptions, LoginStatus, HelperLevel, HelperType


class Helper(models.Model):
    """
    Model for details of people who are willing to help
    """

    # Each helper may belong to more than one category
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    helpline = models.ForeignKey(HelpLine, on_delete=models.CASCADE)
    category = models.ManyToManyField(HelperCategory, blank=True)
    subcategory = models.ManyToManyField(CategorySubcategory, blank=True)
    language = models.ManyToManyField(Language, blank=True)
    helper_number = models.CharField(max_length=16, blank=True, null=True)
    is_anonymous = models.BooleanField(default=True,
                                       help_text=('tells whether helper number is anonymous'))
    gender = models.CharField(max_length=16, blank=True, null=True)
    college_name = models.CharField(max_length=256, blank=True, null=True)
    gcm_canonical_id = models.CharField(max_length=256, blank=True, null=True)
    # Level added to allow task allocation from 2 pools of helpers
    level = models.IntegerField(
        default=HelperLevel.PRIMARY,
        choices=HelperLevel.LEVEL_CHOICES,
    )
    helper_type = models.IntegerField(
        default=HelperType.INDIRECT,
        choices=HelperType.TYPE_CHOICES
    )
    # Rating goes from 0.00 to 5.00
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=2.5)
    created = models.DateTimeField('Created Timestamp', auto_now_add=True)
    last_assigned = models.DateTimeField('Last Assigned Timestamp', auto_now_add=True)
    status = models.IntegerField(
        default=HelperStatusOptions.ACTIVE,
        choices=HelperStatusOptions.STATUS_CHOICES,
    )

    login_status = models.IntegerField(
        default=LoginStatus.PENDING,
        choices=LoginStatus.STATUS_CHOICES,
    )
    
    login_prevstatus = models.IntegerField(
        default=LoginStatus.PENDING,
        choices=LoginStatus.STATUS_CHOICES,
    )

    def __str__(self):
        return str(self.user)

    def get_categories(self):
        return ", ".join([cat.name for cat in self.category.all()])

    def get_languages(self):
        return ", ".join([lang.language for lang in self.language.all()])
