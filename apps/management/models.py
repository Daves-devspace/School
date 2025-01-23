import logging
import os
from datetime import timedelta

from ckeditor.fields import RichTextField

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Avg, Count, Max
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField

from School import settings


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[
            ('Admin', 'Admin'),
            ('Teacher', 'Teacher'),
            ('Headteacher', 'Headteacher'),
            ('Student', 'Student'),
        ],
        default='Student',
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255,default="Unknown Address")
    cv = RichTextField(blank=True, null=True)  # Enables rich text editing
    skills = RichTextField(blank=True, null=True)
    certifications = RichTextField(blank=True, null=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def is_teacher(self):
        return self.role == 'Teacher'

    def is_headteacher(self):
        return self.role == 'Headteacher'

    def is_admin(self):
        return self.role == 'Admin'


class Institution(models.Model):
    name = models.CharField(max_length=250)
    mobile_number = models.CharField(max_length=20)
    email_address = models.CharField(max_length=100)
    address = models.TextField()
    logo = models.FileField(upload_to="logo/%Y/%m/%d", null=True, blank=True)

    def __str__(self):
        return self.name

    def get_logo_path(self):
        if self.logo:
            path = os.path.join(settings.MEDIA_ROOT, self.logo.path)
            print("Logo Path:", path)  # Debugging: Print the logo path
            return path
        return None

    def detail(self, **kwargs):
        details = f"""
            <span style="font-size: 1.4em; color: darkgreen; display: block; margin-bottom: 5px;">
                {self.name}
            </span>
            <span style="display: block; font-size: 1.2em; color: darkgreen;">
                Email: {self.email_address}
            </span>
            <span style="display: block; font-size: 1.2em; color: darkgreen;">
                phone: {self.mobile_number}
            </span>
            
            <span style="display: block; font-size: 1.2em; color: darkgreen;">
                Address: {self.address}
            </span>
        """
        return details


# Term Model
class Term(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Term 1", "Term 2"
    start_date = models.DateField()
    end_date = models.DateField()
    midterm_start_date = models.DateField(null=True, blank=True)
    midterm_end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Term"
        verbose_name_plural = "Terms"
        ordering = ['-start_date']  # Display terms in reverse chronological order (latest first)

    def __str__(self):
        # Display term with its year, e.g., "Term 1 - 2022"
        return f"{self.name} - {self.year}"

    @property
    def year(self):
        """
        Returns the year of the term based on the start_date.
        """
        if self.start_date:
            return self.start_date.year
        return "Unknown Year"  # Fallback if start_date is None

    def get_previous_term(self):
        """
        Retrieves the previous term based on the start_date.
        """
        return Term.objects.filter(start_date__lt=self.start_date).order_by('-start_date').first()

    def get_next_term(self):
        """
        Retrieves the next term based on the start_date.
        """
        return Term.objects.filter(start_date__gt=self.start_date).order_by('start_date').first()

    @property
    def holiday_period(self):
        """
        Calculates the holiday period between the end of this term and the start of the next term.
        """
        next_term = self.get_next_term()
        if next_term:
            return {
                "start": self.end_date + timedelta(days=1),
                "end": next_term.start_date - timedelta(days=1)
            }
        return None  # No holiday period if there is no next term

    @property
    def has_midterm(self):
        """
        Checks if this term has a midterm period defined.
        """
        return self.midterm_start_date is not None and self.midterm_end_date is not None

    @property
    def midterm_break(self):
        """
        Returns the midterm break period if defined.
        """
        if self.has_midterm:
            return {"start": self.midterm_start_date, "end": self.midterm_end_date}
        return None  # No midterm break defined


# TeacherSubject Model
class Subject(models.Model):
    name = models.CharField(max_length=100)
    grade = models.ManyToManyField('students.Grade', blank=True, related_name='subjects')
    single_grade = models.ForeignKey('students.Grade', null=True, blank=True, on_delete=models.SET_NULL, related_name='single_subjects')

    def __str__(self):
        if self.single_grade:
            return f"{self.name} (Only in {self.single_grade.name})"
        grades_list = ", ".join(grade.name for grade in self.grade.all())
        return f"{self.name} ({grades_list})" if grades_list else self.name



# ExamType Model
class ExamType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Midterm", "Final", etc.

    def __str__(self):
        return self.name



# Result Model
# class Result(models.Model):
#     student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='results')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results", default=1)
#     term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="results")
#     score = models.PositiveIntegerField()
#     max_score = models.PositiveIntegerField(default=100)  # New field to store the maximum possible score
#     grade = models.ForeignKey('students.GradeSection', on_delete=models.SET_NULL, null=True, related_name="results")
#
#     class Meta:
#         unique_together = ['student', 'subject', 'term']
#
#     def __str__(self):
#         return f"{self.student.first_name} {self.student.last_name}: {self.subject.name} - {self.score} (Term {self.term.name})"
#
#     @property
#     def year(self):
#         return self.term.year
#
#     @property
#     def percentage(self):
#         """
#         Returns the percentage score normalized to 100.
#         """
#         if self.max_score > 0:
#             return (self.score / self.max_score) * 100
#         return 0


class ReportCard(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards")
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name="report_cards", null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    total_marks = models.FloatField(null=True, blank=True)
    average_marks = models.FloatField(null=True, blank=True)
    grade = models.CharField(max_length=2, null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    attendance_percentage = models.FloatField(null=True, blank=True)
    teacher_remarks = models.TextField(null=True, blank=True)
    conduct_remarks = models.TextField(null=True, blank=True)
    extra_curricular_activities = models.TextField(null=True, blank=True)
    achievements = models.TextField(null=True, blank=True)
    final_comments = models.TextField(null=True, blank=True)
    parent_teacher_meeting_date = models.DateField(null=True, blank=True)
    parent_feedback = models.TextField(null=True, blank=True)

    def calculate_total_marks(self):
        subject_marks = SubjectMark.objects.filter(student=self.student, term=self.term, exam_type=self.exam_type)
        return subject_marks.aggregate(Sum('percentage'))['percentage__sum'] or 0  # Use percentage instead of marks

    def calculate_average_marks(self):
        total_marks = self.calculate_total_marks()
        total_subjects = SubjectMark.objects.filter(student=self.student, term=self.term, exam_type=self.exam_type).count()
        return total_marks / total_subjects if total_subjects else 0  # Average of percentages

    def performance_grade(self):
        avg_marks = self.calculate_average_marks()
        if avg_marks >= 80:
            return "A"
        elif avg_marks >= 60:
            return "B"
        elif avg_marks >= 50:
            return "C"
        else:
            return "D"

    def student_rank(self):
        all_students = (
            ReportCard.objects.filter(term=self.term, exam_type=self.exam_type)
            .annotate(annotated_total_marks=Sum('subject_marks__marks'))  # Renamed annotation
            .order_by('-annotated_total_marks')
        )
        for rank, report in enumerate(all_students, start=1):
            if report.student == self.student:
                return rank
        return None

    def save(self, *args, **kwargs):
        self.total_marks = self.calculate_total_marks()
        self.average_marks = self.calculate_average_marks()
        self.grade = self.performance_grade()
        self.rank = self.student_rank()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.term} - {self.exam_type}"



logger = logging.getLogger(__name__)


class SubjectMark(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subject_marks')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)  # Reuse ExamType
    marks = models.FloatField(null=True, blank=True)  # Marks obtained by the student
    max_score = models.FloatField(default=100)  # Default max score is 100, but it's editable
    percentage = models.FloatField(null=True, blank=True)  # Calculated percentage
    report_card = models.ForeignKey(
        'ReportCard', on_delete=models.CASCADE, related_name='subject_marks', null=True, blank=True
    )

    def save(self, *args, **kwargs):
        # Ensure max_score is positive
        if self.max_score <= 0:
            raise ValueError("Max score must be greater than 0.")

        # Convert marks to percentage if marks are provided
        if self.marks is not None:
            if self.max_score > 0:
                self.percentage = (self.marks / self.max_score) * 100
            else:
                self.percentage = 0
        else:
            self.percentage = None  # Keep percentage None if marks are not provided

        # Auto-create ReportCard if not linked
        if not self.report_card:
            report_card, created = ReportCard.objects.get_or_create(
                student=self.student, term=self.term, exam_type=self.exam_type
            )
            self.report_card = report_card

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'subject', 'term', 'exam_type')

    def __str__(self):
        marks_str = f"{self.marks}/{self.max_score}" if self.marks is not None else "No marks"
        percentage_str = f"{self.percentage:.2f}%" if self.percentage is not None else "No percentage"
        return f"{self.student} - {self.subject} - {self.exam_type} ({marks_str}, {percentage_str})"




# SchoolPerformance Model
class SchoolPerformance(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="school_performance")
    average_score = models.FloatField(editable=False, null=True)
    top_score = models.FloatField(editable=False, null=True)
    total_students = models.PositiveIntegerField(editable=False, null=True)

    def calculate_performance(self):
        scores = SubjectMark.objects.filter(term=self.term).aggregate(
            avg_score=Avg('marks'),
            top_score=Max('marks'),
            total_students=Count('student', distinct=True)
        )
        self.average_score = scores['avg_score'] or 0
        self.top_score = scores['top_score'] or 0
        self.total_students = scores['total_students'] or 0

    def save(self, *args, **kwargs):
        self.calculate_performance()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Performance for {self.term.name}"


class Timetable(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE)
    grade_section = models.ForeignKey("students.GradeSection", on_delete=models.CASCADE, related_name="timetables")
    academic_year = models.CharField(max_length=9, null=True, blank=True)  # Optional field for academic year tracking

    def __str__(self):
        return f"{self.subject.name} ({self.grade_section}) on {self.day}"

    class Meta:
        ordering = ['day', 'start_time']


class Event(models.Model):
    EVENT_TYPES = [
        ('Exam', 'Exam'),
        ('Holiday', 'Holiday'),
        ('Meeting', 'Parent-Teacher Meeting'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    recurring = models.BooleanField(default=False)
    audience = models.CharField(max_length=50,
                                choices=[('students', 'Students'), ('teachers', 'Teachers'), ('both', 'Both')],
                                default='Both')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.event_type})"


class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    participant_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    participant_object_id = models.PositiveIntegerField()
    participant = GenericForeignKey('participant_content_type', 'participant_object_id')

    def __str__(self):
        return f"Participant {self.participant} for Event {self.event}"


class Attendance(models.Model):
    date = models.DateField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Absent')

    class Meta:
        unique_together = ['date', 'event', 'student', 'teacher']


class LessonExchangeRequest(models.Model):
    teacher_1 = models.ForeignKey("teachers.Teacher", related_name="teacher_1", on_delete=models.CASCADE)
    teacher_2 = models.ForeignKey("teachers.Teacher", related_name="teacher_2", on_delete=models.CASCADE)
    lesson_1 = models.ForeignKey(Timetable, related_name="lesson_1", on_delete=models.CASCADE)
    lesson_2 = models.ForeignKey(Timetable, related_name="lesson_2", on_delete=models.CASCADE)
    status = models.CharField(max_length=20,
                              choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                              default='pending')
    conflict = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Check for time conflict between lesson_1 and lesson_2
        if self.lesson_1.day == self.lesson_2.day:
            if not (
                    self.lesson_1.end_time <= self.lesson_2.start_time or self.lesson_2.end_time <= self.lesson_1.start_time):
                raise ValidationError("The selected lessons have overlapping times and cannot be exchanged.")

    def approve_exchange(self):
        """Swap the lessons between teacher_1 and teacher_2"""
        if self.status != 'pending':
            raise ValidationError("Cannot approve an exchange request that is not pending.")

        # Swap the timetable assignments
        lesson_1_teacher = self.lesson_1.teacher
        lesson_2_teacher = self.lesson_2.teacher

        # Ensure that both lessons don't overlap after the exchange
        lesson_1_teacher.timetables.filter(
            day=self.lesson_1.day,
            start_time__lt=self.lesson_1.end_time,  # Check for time overlap
            end_time__gt=self.lesson_1.start_time
        ).exclude(pk=self.lesson_1.pk)

        lesson_2_teacher.timetables.filter(
            day=self.lesson_2.day,
            start_time__lt=self.lesson_2.end_time,
            end_time__gt=self.lesson_2.start_time
        ).exclude(pk=self.lesson_2.pk)

        # Swap the lessons
        self.lesson_1.teacher = lesson_2_teacher
        self.lesson_2.teacher = lesson_1_teacher
        self.lesson_1.save()
        self.lesson_2.save()

        self.status = 'approved'
        self.save()


def validate_google_meet_url(value):
    if not value.startswith('https://meet.google.com/'):
        raise ValidationError("Please enter a valid Google Meet link.")

class HolidayPresentation(models.Model):
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='presentations/', blank=True, null=True)
    live_link = models.URLField(max_length=500, blank=True, null=True)  # For live meeting links
    embed_code = models.TextField(blank=True, null=True,validators=[validate_google_meet_url])  # For embedding external slides
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user_profile.user.username}"

class Feedback(models.Model):
    presentation = models.ForeignKey(HolidayPresentation, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who gave the feedback
    comment = models.TextField()
    rating = models.IntegerField(default=0)  # Optional: Scoring system (e.g., 1–5 stars)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Feedback by {self.user.username} on {self.presentation.title}"


class Notification(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)  # To track if the notification has been read

    def __str__(self):
        return f"Notification from {self.sender.username} to {self.recipient.username}"