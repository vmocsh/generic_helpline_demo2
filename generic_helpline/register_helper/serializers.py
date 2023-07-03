"""
Serializers required for register_helper
"""

from rest_framework import serializers

from .models import Helper


class HelperSerializer(serializers.ModelSerializer):
    """
    Serializer for Helper model
    """
    class Meta:
        """
        Meta class to specify the serializer attributes
        """
        model = Helper
        fields = ("helper_number", "gcm_canonical_id",)
