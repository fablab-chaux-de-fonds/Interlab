from rest_framework import serializers
from .models import OpeningSlot

class OpeningSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningSlot
        fields = "__all__"
