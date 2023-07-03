from rest_framework import serializers
from wwh_form_delivery.models import WhatsAppUser, WhatsAppMessage


class WhatsAppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppUser
        fields = ['contact', 'otp', 'is_updated']


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppMessage
        fields = '__all__'
