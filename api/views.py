from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics

from rest_framework.authentication import TokenAuthentication
from .permissions import IsInApiGroup

from accounts.models import CustomUser, Subscription, Profile
from fabcal.models import OpeningSlot, MachineSlot
from openings.models import Opening

from .serializers import OpeningSlotSerializer, MachineSlotSerializer
from .serializers import CustomUserSerializer
from .serializers import OpeningSerializer
from .serializers import SubscriptionSerializer
from .serializers import ProfileSerializer

class OpeningSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = Opening.objects.all()
    serializer_class = OpeningSerializer

class OpeningSlotSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = OpeningSlot.objects.all()
    serializer_class = OpeningSlotSerializer

class MachineSlotSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = MachineSlot.objects.all()
    serializer_class = MachineSlotSerializer

class CustomUserSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class SubscriptionSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

class ProfileSet(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsInApiGroup]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer