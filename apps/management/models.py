import logging
import os
from datetime import timedelta, datetime
from datetime import date

from django.conf import settings
from django.contrib.auth.models import User

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Avg, Count, Max, Value, FloatField
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField

from School import settings
from django_ckeditor_5.fields import CKEditor5Field

# Each tuple contains (threshold, grade_letter)
GRADE_MAPPING = [
    (80, "EE"),
    (50, "ME"),
    (30, "AE"),
]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=[('Admin', 'Admin'), ('Teacher', 'Teacher'), ('Headteacher', 'Headteacher'), ('Student', 'Student')],
        default='Student',
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    address = models.CharField(max_length=255, default="Unknown Address")
    cv = CKEditor5Field(config_name='default', blank=True, null=True)
    skills = CKEditor5Field(config_name='default', blank=True, null=True)
    certifications = CKEditor5Field(config_name='default', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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


class Term(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Term 1", "Term 2"
    start_date = models.DateField()
    end_date = models.DateField()
    midterm_start_date = models.DateField(null=True, blank=True)
    midterm_end_date = models.DateField(null=True, blank=True)
    year = models.PositiveIntegerField(default=timezone.now().year)  # Default to current year

    class Meta:
        verbose_name = "Term"
        verbose_name_plural = "Terms"
        ordering = ['-year']  # Display terms in reverse chronological order (latest first)

    def __str__(self):
        return f"{self.name}-{self.year}"

    def get_previous_term(self):
        return Term.objects.filter(start_date__lt=self.start_date).order_by('-start_date').first()

    def get_next_term(self):
        return Term.objects.filter(start_date__gt=self.start_date).order_by('start_date').first()

    @property
    def holiday_period(self):
        next_term = self.get_next_term()
        if next_term:
            return {
                "start": self.end_date + timedelta(days=1),
                "end": next_term.start_date - timedelta(days=1)
            }
        return None

    @property
    def has_midterm(self):
        return self.midterm_start_date is not None and self.midterm_end_date is not None

    @property
    def midterm_break(self):
        if self.has_midterm:
            return {"start": self.midterm_start_date, "end": self.midterm_end_date}
        return None

    def clean(self):
        if Term.objects.exclude(id=self.id).filter(name=self.name, year=self.year).exists():
            raise ValidationError(f"A term with the name '{self.name}' for the year {self.year} already exists.")

        overlapping_terms = Term.objects.exclude(id=self.id).filter(
            year=self.year,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        )
        if overlapping_terms.exists():
            raise ValidationError(f"The term '{self.name}' for the year {self.year} overlaps with an existing term.")

        super().clean()

    @property
    def progress_percentage(self):
        """
        Calculates the progress percentage of the term based on the current date.
        Returns a value between 0 and 100.
        """
        current_date = timezone.now().date()

        if current_date < self.start_date:
            return 0  # Term hasn't started yet
        elif current_date > self.end_date:
            return 100  # Term has ended

        # Calculate the percentage of time passed between the start and end date of the term
        total_duration = self.end_date - self.start_date
        elapsed_time = current_date - self.start_date
        progress = (elapsed_time / total_duration) * 100

        return round(progress, 2)


# ExamType Model
class ExamType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Midterm", "Final", etc.

    def __str__(self):
        return self.name


class ReportCard(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards")
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name="report_cards", null=True,
                                  blank=True)
    year = models.IntegerField(editable=False)  # Auto-set based on Term
    created_at = models.DateField(auto_now_add=True)
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

    def save(self, *args, **kwargs):
        """Ensure year is set from the term before saving."""
        if self.term and not self.year:
            self.year = self.term.year  # Auto-set year from the Term model
        super().save(*args, **kwargs)  # Save instance first

    def calculate_total_marks(self):
        """Calculate total marks for subjects under this report card and exam type."""
        if not self.pk:
            return 0.0  # Return 0 if the instance is not saved

        result = SubjectMark.objects.filter(report_card=self).aggregate(
            total_marks=Coalesce(Sum('marks'), Value(0.0, output_field=FloatField()))
        )
        return result['total_marks']

    def calculate_average_marks(self):
        """Calculate the average marks per exam type, counting subjects with marks=None as 0."""
        total_marks = self.calculate_total_marks()
        total_subjects = SubjectMark.objects.filter(report_card=self).count()
        return round(total_marks / total_subjects) if total_subjects > 0 else 0.0

    def performance_grade(self):
        """Determine the grade based on the average marks."""
        avg_marks = self.calculate_average_marks()
        for threshold, grade in GRADE_MAPPING:
            if avg_marks >= threshold:
                return grade
        # Fallback if avg_marks is below the lowest threshold (i.e., below 30)
        return "BE"

    def student_rank(self, filter_by_grade=False):
        """
        Determine the student's rank based on:
        - If filtering by `grade_section`, rank within the same section.
        - If filtering by `grade`, rank within all sections of the same grade.
        """
        if not self.pk:
            return None

        # Default: Rank by grade_section
        student_filter = {'student__grade': self.student.grade}

        # If ranking by grade instead, adjust the filter
        if filter_by_grade:
            student_filter = {'student__grade__grade': self.student.grade.grade}  # Use grade from grade_section

        # Fetch all students in the filtered category (grade or grade_section)
        all_students = (
            ReportCard.objects.filter(
                term=self.term,
                exam_type=self.exam_type,
                year=self.year,
                **student_filter  # Dynamically filter
            )
            .order_by('-total_marks')
        )

        previous_marks = None
        rank = 0
        actual_rank = 0

        for report in all_students:
            actual_rank += 1
            if report.total_marks != previous_marks:
                rank = actual_rank  # Update rank only if marks change
            previous_marks = report.total_marks

            if report.student == self.student:
                return rank

        return None

    def __str__(self):
        return f"{self.student} - {self.term} - {self.exam_type} - {self.year}"


# ✅ FIX: Prevent recursion by updating fields only if they have changed
@receiver(post_save, sender=ReportCard)
def update_report_card_fields(sender, instance, created, **kwargs):
    # Get new calculated values
    new_total_marks = instance.calculate_total_marks()
    new_average_marks = instance.calculate_average_marks()
    new_grade = instance.performance_grade()
    new_rank = instance.student_rank()

    # ✅ Check if any field actually needs updating before saving
    if (
            instance.total_marks != new_total_marks or
            instance.average_marks != new_average_marks or
            instance.grade != new_grade or
            instance.rank != new_rank
    ):
        # Update fields **without triggering another save() call**
        ReportCard.objects.filter(pk=instance.pk).update(
            total_marks=new_total_marks,
            average_marks=new_average_marks,
            grade=new_grade,
            rank=new_rank
        )


class SubjectMark(models.Model):
    report_card = models.ForeignKey(
        'ReportCard',
        on_delete=models.CASCADE,
        related_name='subject_marks'
    )
    subject = models.ForeignKey(
        'schedules.Subject',
        on_delete=models.CASCADE,
        related_name='subject_marks'
    )
    marks = models.FloatField(null=True, blank=True)
    max_score = models.FloatField(default=100)
    percentage = models.FloatField(null=True, blank=True)

    # Only one extra field for the subject's letter grade.
    subject_grade = models.CharField(max_length=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.max_score <= 0:
            raise ValueError("Max score must be greater than 0.")

        # Calculate the percentage if marks are provided.
        if self.marks is not None:
            self.percentage = round((self.marks / self.max_score) * 100)
        else:
            self.percentage = None

        # Determine the grade using the mapping.
        if self.percentage is None:
            self.subject_grade = None
        else:
            for threshold, grade in GRADE_MAPPING:
                if self.percentage >= threshold:
                    self.subject_grade = grade
                    break
            else:
                # Fallback: if percentage is below 30, assign "BE"
                self.subject_grade = "BE"

        super().save(*args, **kwargs)
        # Update the related ReportCard if necessary.
        self.report_card.save()

    class Meta:
        unique_together = ('report_card', 'subject')

    def __str__(self):
        marks_str = f"{self.marks}/{self.max_score}" if self.marks is not None else "No marks"
        percentage_str = f"{self.percentage:.2f}%" if self.percentage is not None else "No percentage"
        grade_str = f"Grade {self.subject_grade}" if self.subject_grade else "No grade"
        return f"{self.report_card.student} - {self.subject} ({marks_str}, {percentage_str}, {grade_str})"


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
    subject = models.ForeignKey('schedules.Subject', on_delete=models.CASCADE)
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
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    section = models.ForeignKey('students.GradeSection', on_delete=models.CASCADE,default='section')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE,default="class_teacher")
    date = models.DateField()
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    absence_reason = models.TextField(blank=True, null=True)


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
    embed_code = models.TextField(blank=True, null=True,
                                  validators=[validate_google_meet_url])  # For embedding external slides
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


# class Notification(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
#     recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")
#     title = models.CharField(max_length=255)
#     message = models.TextField()
#     created_at = models.DateTimeField(default=now)
#     is_read = models.BooleanField(default=False)  # To track if the notification has been read
#
#     def __str__(self):
#         return f"Notification from {self.sender.username} to {self.recipient.username}"


# # Model for a Teacher (Assumes you have a teacher model or user system in place)
# class Teacher(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     subject = models.CharField(max_length=100)
#     phone_number = models.CharField(max_length=15)
#
#     def __str__(self):
#         return self.user.get_full_name()
#
# # Model for a Student
# class Student(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     grade = models.CharField(max_length=10)
#     date_of_birth = models.DateField()
#
#     def __str__(self):
#         return self.user.get_full_name()

# Model for Club Leadership Roles
class ClubRole(models.Model):
    club = models.ForeignKey('Club', on_delete=models.CASCADE, related_name='club_roles')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[('President', 'President'), ('Vice President', 'Vice President'),
                                                    ('Secretary', 'Secretary'), ('Treasurer', 'Treasurer')])
    date_assigned = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.student} - {self.role} in {self.club}"


# Model for Club Attendance
class ClubAttendance(models.Model):
    club = models.ForeignKey('Club', on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=20,
                              choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Excused', 'Excused')])

    def __str__(self):
        return f"{self.student} - {self.status} on {self.date}"


# Model for Club Events
class ClubEvent(models.Model):
    club = models.ForeignKey('Club', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    event_time = models.TimeField()
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"Event: {self.title} on {self.event_date}"


# Model for Club Reports
class ClubReport(models.Model):
    club = models.ForeignKey('Club', on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    report = models.TextField()

    def __str__(self):
        return f"Report for {self.club.name} on {self.date}"


# Model for Club Feedback (for Students)
class ClubFeedback(models.Model):
    club = models.ForeignKey('Club', on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    feedback = models.TextField()
    date_submitted = models.DateField(default=date.today)

    def __str__(self):
        return f"Feedback from {self.student} for {self.club.name}"


# Model for a Club
class Club(models.Model):
    name = models.CharField(max_length=200)  # Name of the club
    description = models.TextField()  # A brief description of the club
    teachers = models.ManyToManyField('teachers.Teacher', related_name='clubs')  # Teacher overseeing the club
    members = models.ManyToManyField('students.Student', related_name='clubs')  # List of students in the club
    meeting_time = models.CharField(max_length=50)  # Time the club meets (e.g., "Mondays at 3 PM")
    created_at = models.DateTimeField(auto_now_add=True)  # When the club was created

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
