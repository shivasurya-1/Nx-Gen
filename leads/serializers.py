from rest_framework import serializers
from .models import ContactUs, DemoSchedule
from datetime import date

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'



class DemoScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoSchedule
        fields = "__all__"