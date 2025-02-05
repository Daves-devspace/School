
from django import forms
from django.forms import TimeInput
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Term, SubjectMark, Timetable, LessonExchangeRequest, Profile, HolidayPresentation, Feedback, \
    ExamType
from ..schedules.models import Subject
from ..students.models import Student, Book, GradeSection, Grade
from ..teachers.models import Teacher

class ProfileForm(forms.ModelForm):
    cv = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    skills = forms.CharField(widget=CKEditor5Widget(config_name='default'))
    certifications = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = Profile
        fields = '__all__'

class TermForm(forms.ModelForm):
    class Meta:
       model = Term
       fields = ['name','start_date','end_date','midterm_start_date','midterm_end_date']
       widgets = {
           'name':forms.TextInput(attrs={'class':'form-control','placeholder':'Term Name'}),
           'start_date':forms.DateInput(attrs={'class':'form-control','type':'date'}),
           'end_date':forms.DateInput(attrs={'class':'form-control','type':'date'}),
           'midterm_start_date':forms.DateInput(attrs={'class':'form-control','type':'date'}),
           'midterm_end_date':forms.DateInput(attrs={'class':'form-control','type':'date'}),

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





# class PerformanceFilterForm(forms.Form):
#     grade = forms.ModelChoiceField(
#         queryset=Grade.objects.all(),
#         required=True,
#     )
#     term = forms.ModelChoiceField(queryset=Term.objects.all(), required=True)
#     exam_type = forms.ModelChoiceField(queryset=ExamType.objects.all(), required=True)
#     grade_section = forms.ModelChoiceField(queryset=GradeSection.objects.all(), required=False)
#     subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False)

class PerformanceFilterForm(forms.Form):
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        required=False,
        empty_label="Select Grade",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    grade_section = forms.ModelChoiceField(
        queryset=GradeSection.objects.all(),
        required=False,
        empty_label="Select Grade Section",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        required=True,
        empty_label="Select Term",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    exam_type = forms.ModelChoiceField(
        queryset=ExamType.objects.all(),
        required=True,
        empty_label="Select Exam Type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get('grade')
        grade_section = cleaned_data.get('grade_section')

        if not grade and not grade_section:
            raise forms.ValidationError("Please select either a Grade or a Grade Section.")

        return cleaned_data



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

class ExamTypeForm(forms.ModelForm):
    class Meta:
        model = ExamType
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
        }




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