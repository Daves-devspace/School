from rest_framework import serializers, generics

from apps.management.models import Subject, Timetable, Event, EventParticipant
from apps.students.models import GradeSection
from apps.teachers.models import TeacherAssignment


#teacher management
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class GradeSectionSerializer(serializers.ModelSerializer):
    grade = serializers.StringRelatedField()
    section = serializers.StringRelatedField()

    class Meta:
        model = GradeSection
        fields = ['id', 'grade', 'section']

class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.StringRelatedField()
    subject = SubjectSerializer()
    grade_section = GradeSectionSerializer()

    class Meta:
        model = TeacherAssignment
        fields = ['id', 'teacher', 'subject', 'grade_section', 'assigned_date']

class CreateTeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAssignment
        fields = ['teacher', 'subject', 'grade_section']

class TeacherAssignmentCreateView(generics.CreateAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = CreateTeacherAssignmentSerializer




#student timetable
class TimetableSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    teacher = serializers.StringRelatedField()
    grade_section = GradeSectionSerializer()

    class Meta:
        model = Timetable
        fields = ['id', 'day', 'start_time', 'end_time', 'subject', 'teacher', 'grade_section']


#events
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'event_type', 'date', 'time', 'recurring']

class EventParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventParticipant
        fields = ['event', 'participant_content_type', 'participant_object_id']

