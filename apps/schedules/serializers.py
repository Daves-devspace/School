from rest_framework import serializers
from .models import Teacher, Subject, TeacherAssignment
from ..students.models import GradeSection


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'full_name', 'email', 'get_display_name']  # Adjust fields as necessary


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']  # Adjust fields as necessary


class GradeSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSection
        fields = ['id', 'grade', 'section']  # Adjust fields as necessary


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer()
    subject = SubjectSerializer()
    grade_section = GradeSectionSerializer()

    class Meta:
        model = TeacherAssignment
        fields = ['id', 'teacher', 'subject', 'grade_section', 'assigned_date']
