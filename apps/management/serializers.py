
from rest_framework import serializers
from .models import Event, ClubEvent

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_type', 'date', 'time', 'description', 'audience']

class ClubEventSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)  # Include club name

    class Meta:
        model = ClubEvent
        fields = ['id', 'title', 'description', 'event_date', 'event_time', 'location', 'club_name']
