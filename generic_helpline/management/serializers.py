"""
Serializers required for Helplines
"""

from rest_framework import serializers
from .models import HelpLine, HelperCategory
from ivr.models import Language


class HelplineSerializer(serializers.ModelSerializer):
    """
    Serializer for Helpline model
    """
    class Meta:
        """
        Meta class to specify the serializer attributes
        """
        model = HelpLine
        fields = ("name", "helpline_number",)


class HelperCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Helper model
    """
    class Meta:
        """
        Meta class to specify the serializer attributes
        """
        model = HelperCategory
        fields = ("name",)


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializer for Helper model
    """
    class Meta:
        """
        Meta class to specify the serializer attributes
        """
        model = Language
        fields = ("language",)
