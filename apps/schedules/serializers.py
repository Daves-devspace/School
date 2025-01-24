from rest_framework import serializers
from .models import Instructor, Course, Room, TimetableSlot, TimeSlot


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ['instructor_id', 'name', 'subjects_grades']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_id', 'course_name', 'department', 'grades', 'requires_special_room', 'special_room_name']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['room_id', 'room_name', 'is_special']


class TimeSlotSerializer(serializers.ModelSerializer):
    # Only include the time_range instead of the whole TimeSlot object
    time_range = serializers.CharField(source='time_slot', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['time_range']

class TimetableSlotSerializer(serializers.ModelSerializer):
    # Directly show the time_range from the TimeSlot model
    time_range = serializers.CharField(source='time_slot.time_range', read_only=True)

    class Meta:
        model = TimetableSlot
        fields = ['course', 'instructor', 'room', 'day_of_week', 'time_range']
