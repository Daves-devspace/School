from django.forms import ModelForm
from django.forms.widgets import TimeInput

from. models import *
from django import forms


from ..teachers.models import Department
from django.apps import apps

Grade = apps.get_model('students', 'Grade')
GradeSection = apps.get_model('students', 'GradeSection')

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'grade',  'department', 'requires_special_room', 'special_room']

    # Dropdown for selecting multiple grades
    grade = forms.ModelMultipleChoiceField(
        queryset=Grade.objects.all(),
        widget=forms.SelectMultiple,
        required=False  # Optional if the subject applies to multiple grades
    )

    # Dropdown for selecting a single grade
    # single_grade = forms.ModelChoiceField(
    #     queryset=Grade.objects.all(),
    #     required=False,
    #     empty_label="Select a grade (optional)"
    # )

    # Text input for department
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter department (optional)'})
    )

    # Checkbox for requires special room
    requires_special_room = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput()
    )

    # Dropdown for selecting a special room (optional)
    special_room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        required=False,
        empty_label="Select a special room (optional)"
    )


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_name', 'is_special', 'related_subjects', 'grade_section']

    room_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter room name'})
    )

    is_special = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    related_subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        required=False
    )

    grade_section = forms.ModelChoiceField(
        queryset=GradeSection.objects.all(),
        required=False,
        empty_label="Select a grade section (optional)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )



class SubjectPreferenceForm(forms.ModelForm):
    class Meta:
        model = SubjectPreference
        fields = ['subject', 'grade_section', 'sessions_per_week', 'is_core_subject']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'grade_section': forms.Select(attrs={'class': 'form-control'}),
            'sessions_per_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_core_subject': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }







#
# class RoomForm(ModelForm):
#     class Meta:
#         model = Room
#         labels = {
#             "r_number": "Room ID",
#             "seating_capacity": "Capacity"
#         }
#         fields = [
#             'r_number',
#             'seating_capacity'
#         ]
#
#
# class InstructorForm(ModelForm):
#     class Meta:
#         model = Instructor
#         labels = {
#             "uid": "Teacher UID",
#             "name": "Full Name"
#         }
#         fields = [
#             'uid',
#             'name',
#         ]
#
#
# class MeetingTimeForm(ModelForm):
#     class Meta:
#         model = MeetingTime
#         fields = [
#             'pid',
#             'time',
#             'day'
#         ]
#         widgets = {
#             'pid': forms.TextInput(),
#             'time': forms.Select(),
#             'day': forms.Select(),
#         }
#         labels = {
#             "pid": "Meeting ID",
#             "time": "Time",
#             "day": "Day of the Week"
#         }
#
#
# class CourseForm(ModelForm):
#     class Meta:
#         model = Course
#         fields = ['course_number', 'course_name', 'max_numb_students', 'instructors']
#         labels = {
#             "course_number": "Course ID",
#             "course_name": "Course Name",
#             "max_numb_students": "Course Capacity",
#             "instructors": "Course Teachers"
#         }
#
#
# class DepartmentForm(ModelForm):
#     class Meta:
#         model = Department
#         fields = ['dept_name', 'courses']
#         labels = {
#             "dept_name": "Department Name",
#             "courses": "Corresponding Courses"
#         }
#
#
# class SectionForm(ModelForm):
#     class Meta:
#         model = Section
#         fields = ['section_id', 'department', 'num_class_in_week']
#         labels = {
#             "section_id": "Section ID",
#             "department": "Corresponding Department",
#             "num_class_in_week": "Classes Per Week"
#         }
