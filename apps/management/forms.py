from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import TimeInput

from .models import Term, SubjectMark, Timetable, LessonExchangeRequest, Profile, HolidayPresentation, Feedback
from ..schedules.models import Subject
from ..students.models import Student, Book, GradeSection, Grade
from ..teachers.models import Teacher

class ProfileForm(forms.ModelForm):
    cv = forms.CharField(widget=CKEditorWidget(), required=False)
    skills = forms.CharField(widget=CKEditorWidget(), required=False)
    certifications = forms.CharField(widget=CKEditorWidget(), required=False)

    class Meta:
        model = Profile
        fields = '__all__'

class TermForm(forms.ModelForm):
    class Meta:
       model = Term
       fields = ['name','start_date','end_date','midterm_start_date','midterm_end_date']
       widgets = {
           'name':forms.TextInput(attrs={'class':'form-control','placeholder':'Term Name'}),
           'start_date':forms.TimeInput(attrs={'class':'form-control','type':'time'}),
           'end_date':forms.TimeInput(attrs={'class':'form-control','type':'time'}),
           'midterm_start_date':forms.TimeInput(attrs={'class':'form-control','type':'time'}),
           'midterm_end_date':forms.TimeInput(attrs={'class':'form-control','type':'time'}),

       }




class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title','author','year','subject','isbn']
        widgets = {
            'title':forms.TextInput(attrs={'class':'form-control','placeholder':'Book Title'}),
            'author':forms.TextInput(attrs={'class':'form-control'}),
            'year':forms.DateInput(attrs={'type':'date'}),
            'subject':forms.TextInput(attrs={'class':'form-control'}),
            'isbn':forms.TextInput(attrs={'class':'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'grade', 'single_grade']  # Include both fields

    # Dropdown for selecting multiple grades (optional: you can use a multiple select dropdown)
    grade = forms.ModelMultipleChoiceField(
        queryset=Grade.objects.all(),  # Display all grades to choose from
        widget=forms.SelectMultiple,  # Use a multiple select dropdown (for multiple grades)
        required=False  # Make this field optional if the subject is for only one grade
    )

    # Dropdown for selecting a single grade (e.g., for Comp)
    single_grade = forms.ModelChoiceField(
        queryset=Grade.objects.all(),  # Display all grades to choose from
        required=False,  # Make this field optional if the subject belongs to multiple grades
        empty_label="Select a grade (optional)"
    )


class AddResultForm(forms.ModelForm):
    class_name = forms.ModelChoiceField(queryset=GradeSection.objects.all(), required=True, label="Class Section")
    student = forms.ModelChoiceField(queryset=Student.objects.none(), required=True, label="Student")
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=True, label="Subject")
    marks = forms.IntegerField(min_value=0, max_value=100, required=True, label="Marks")

    class Meta:
        model = SubjectMark
        fields = ['class_name', 'student', 'subject', 'marks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically update the student queryset based on the selected class_name (GradeSection)
        if 'class_name' in self.initial:
            class_section_id = self.initial['class_name']
            self.fields['student'].queryset = Student.objects.filter(grade_section_id=class_section_id)
        elif 'class_name' in self.data:  # Check if 'class_name' was selected in POST data
            class_section_id = self.data.get('class_name')
            self.fields['student'].queryset = Student.objects.filter(grade_section_id=class_section_id)
        else:
            self.fields['student'].queryset = Student.objects.none()



class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['grade_section', 'subject', 'teacher', 'day', 'start_time', 'end_time']
        widgets = {
            'grade_section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'start_time': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    # Overriding the 'day' field to ensure it uses the correct choices and renders as a dropdown
    day = forms.ChoiceField(
        choices=Timetable.DAYS_OF_WEEK,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Start time must be earlier than end time.")

        return cleaned_data





class LessonExchangeForm(forms.ModelForm):
    teacher_1 = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,  # Required only for admins
        help_text="Select the first teacher (admin only)."
    )
    teacher_2 = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,  # Required only for admins
        help_text="Select the second teacher (admin only)."
    )

    class Meta:
        model = LessonExchangeRequest
        fields = ['lesson_1', 'lesson_2', 'teacher_1', 'teacher_2']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Pass the user to the form
        super().__init__(*args, **kwargs)

        # Customize behavior based on user role
        if hasattr(user, 'teacher'):  # If the user is a teacher
            self.fields['teacher_1'].widget = forms.HiddenInput()  # Hide teacher_1
            self.fields['teacher_1'].initial = user.teacher  # Set teacher_1 to logged-in teacher
            self.fields['teacher_2'].queryset = Teacher.objects.exclude(pk=user.teacher.pk)  # Exclude self
            self.fields['teacher_2'].required = True  # Ensure teacher_2 is selected

        else:  # If the user is an admin
            self.fields['teacher_1'].required = True
            self.fields['teacher_2'].required = True



class HolidayPresentationForm(forms.ModelForm):
    class Meta:
        model = HolidayPresentation
        fields = ['title', 'description', 'file', 'live_link', 'embed_code']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter presentation title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter a description'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'live_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste your live meeting link (e.g., Google Meet)'}),
            'embed_code': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Paste embed code for external slides (e.g., Google Slides, PowerPoint)'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['presentation', 'comment', 'rating']

    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Leave feedback...'}))
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.NumberInput(attrs={'class': 'form-control'}))