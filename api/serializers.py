from rest_framework import serializers
from accounts.models import CustomUser, Subscription, Profile
from fabcal.models import OpeningSlot, MachineSlot
from openings.models import Opening

class OpeningSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Opening
        fields = ['id', 'title']

class OpeningSlotSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta: 
        model = OpeningSlot
        fields = ['id', 'start', 'end', 'created_at', 'user', 'opening_id', 'duration']

    def get_duration(self, obj):
        return obj.get_duration

class MachineSlotSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta: 
        model = MachineSlot
        fields = ['id', 'start', 'end', 'created_at', 'updated_at', 'user', 'duration']

    def get_duration(self, obj):
        return obj.get_duration

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CustomUser
        fields = ['id', 'last_login', 'first_name', 'last_name', 'date_joined', 'email']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Subscription
        fields = ['id', 'start', 'end']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Profile
        fields = ['user', 'subscription']