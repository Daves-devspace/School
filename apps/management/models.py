import logging
import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Avg, Count, Max

from School import settings


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Institution(models.Model):
    name =  models.CharField(max_length=250)
    mobile_number = models.CharField(max_length=20)
    email_address = models.CharField(max_length=100)
    address = models.TextField()
    logo = models.FileField(upload_to="logo/%Y/%m/%d",null=True,blank=True)

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
    midterm_start_date = models.DateField(null=True, blank=True)  # Optional
    midterm_end_date = models.DateField(null=True, blank=True)    # Optional

    class Meta:
        verbose_name = "Term"
        verbose_name_plural = "Terms"
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} - {self.start_date} to {self.end_date}"

    @property
    def year(self):
        # Returns the year of the term
        return self.start_date.year

    def get_previous_term(self):
        return Term.objects.filter(start_date__lt=self.start_date).order_by('-start_date').first()

    def get_next_term(self):
        return Term.objects.filter(start_date__gt=self.start_date).order_by('start_date').first()

    @property
    def holiday_period(self):
        """
        Returns the holiday period (start_date and end_date) between this term and the next term.
        """
        next_term = self.get_next_term()
        if next_term:
            holiday_start = self.end_date + timedelta(days=1)
            holiday_end = next_term.start_date - timedelta(days=1)
            return {"start": holiday_start, "end": holiday_end}
        return None

    @property
    def has_midterm(self):
        """
        Returns True if midterm dates are set, otherwise False.
        """
        return self.midterm_start_date is not None and self.midterm_end_date is not None

    @property
    def midterm_break(self):
        """
        Returns the midterm break period (start_date and end_date) if it exists.
        """
        if self.has_midterm:
            return {
                "start": self.midterm_start_date,
                "end": self.midterm_end_date
            }
        return None


# TeacherSubject Model
class Subject(models.Model):
    name = models.CharField(max_length=100)
    grade = models.ManyToManyField('students.Grade', blank=True, related_name='subjects')  # Many-to-many for subjects taught across multiple grades
    single_grade = models.ForeignKey('students.Grade', null=True, blank=True, on_delete=models.SET_NULL, related_name='single_subjects')  # Foreign key for subjects taught in a single grade (e.g., Comp for Grade 5)

    def __str__(self):
        if self.single_grade:
            return f"{self.name} (Only in {self.single_grade.name})"
        else:
            grades_list = ", ".join(grade.name for grade in self.grade.all())
            return f"{self.name} ({grades_list})" if grades_list else self.name



# ExamType Model
class ExamType(models.Model):
    name = models.CharField(max_length=50)  # E.g., "Opener", "Mid-Term", "End-Term"
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exam_types')
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'term')

    def __str__(self):
        return f"{self.name} - {self.term}"


# Result Model
class Result(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results", default=1)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="results")
    score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField(default=100)  # New field to store the maximum possible score
    grade = models.ForeignKey('students.GradeSection', on_delete=models.SET_NULL, null=True, related_name="results")

    class Meta:
        unique_together = ['student', 'subject', 'term']

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name}: {self.subject.name} - {self.score} (Term {self.term.name})"

    @property
    def year(self):
        return self.term.year

    @property
    def percentage(self):
        """
        Returns the percentage score normalized to 100.
        """
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0




class ReportCard(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards")
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, related_name="report_cards", null=True,
                                  blank=True)
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
        return subject_marks.aggregate(Sum('marks'))['marks__sum'] or 0

    def calculate_average_marks(self):
        total_marks = self.calculate_total_marks()
        total_subjects = SubjectMark.objects.filter(student=self.student, term=self.term,
                                                    exam_type=self.exam_type).count()
        return total_marks / total_subjects if total_subjects else 0

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
            .annotate(annotated_total_marks=Sum('student__subjectmark__marks'))  # Changed annotation name
            .order_by('-annotated_total_marks')
        )
        for rank, report in enumerate(all_students, start=1):
            if report.student == self.student:
                return rank
        return None

    def __str__(self):
        term_name = self.term.name if self.term else "No Term"
        exam_type_name = self.exam_type.name if self.exam_type else "No Exam Type"
        student_name = self.student.first_name if self.student else "No Student"
        return f"{student_name} - {term_name} - {exam_type_name}"



logger = logging.getLogger(__name__)
# SubjectMark Model
class SubjectMark(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE,related_name='subject_marks')
    term = models.ForeignKey('Term', on_delete=models.CASCADE)
    exam_type = models.ForeignKey('ExamType', on_delete=models.CASCADE)
    marks = models.FloatField()
    report_card = models.ForeignKey(
        'ReportCard',
        on_delete=models.CASCADE,
        related_name='subject_marks',
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        try:
            self.marks = float(self.marks)
            if not 0 <= self.marks <= 100:
                raise ValueError("Marks must be between 0 and 100.")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid marks for student {self.student}: {e}")
            raise ValueError("Marks must be a valid number between 0 and 100.")

        # Auto-create ReportCard
        if not self.report_card:
            report_card, created = ReportCard.objects.get_or_create(
                student=self.student, term=self.term, exam_type=self.exam_type
            )
            self.report_card = report_card

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'subject', 'term', 'exam_type')

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam_type} ({self.marks:.2f})"





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
    audience = models.CharField(max_length=50, choices=[('students', 'Students'), ('teachers', 'Teachers'), ('both', 'Both')],default='Both')
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
    event = models.ForeignKey(Event, on_delete=models.CASCADE,null=True, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')],default='Absent')

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