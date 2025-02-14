# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models


from apps.teachers.models import Teacher, TeacherAssignment
User = get_user_model()

# Model for Instructor (Teacher)
# class Instructor(models.Model):
#     instructor_id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=100)
#     subjects_grades = models.JSONField()  # A JSON field to store the subjects each instructor teaches and for which grades
#
#     def __str__(self):
#         return self.name

# Model for Course (Subject)
class Subject(models.Model):
    name = models.CharField(max_length=100)  # Name of the subject (e.g., English, Math, etc.)

    # Many-to-many relationship to Grade, as a subject can be taught across multiple grades
    grade = models.ManyToManyField('students.Grade', blank=True, related_name='subjects_schedules')

    # Department and special room details
    department = models.ForeignKey('teachers.Department', on_delete=models.SET_NULL, max_length=100, blank=True, null=True)
    requires_special_room = models.BooleanField(
        default=False  # Whether the subject needs a special room (e.g., computer lab)
    )
    special_room = models.ForeignKey(
        'Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='subject_special_rooms'
    )  # Reference to the special room if required

    def __str__(self):
        grades_list = ", ".join(grade.name for grade in self.grade.all())
        return f"{self.name} ({grades_list})" if grades_list else self.name



class SubjectPreference(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_section = models.ForeignKey('students.GradeSection', on_delete=models.CASCADE)
    sessions_per_week = models.PositiveIntegerField(default=3)
    is_core_subject = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject.name} ({self.grade_section}) - {self.sessions_per_week} sessions/week"



class Room(models.Model):
    room_name = models.CharField(max_length=100)
    is_special = models.BooleanField(default=False)
    related_subjects = models.ManyToManyField('Subject', blank=True)
    grade_section = models.ForeignKey(
        'students.GradeSection',
        on_delete=models.CASCADE,
        related_name='rooms',
        null=True,  # Allow null for non-related rooms
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['grade_section', 'is_special'],
                condition=models.Q(is_special=False),
                name='unique_default_room_per_grade_section'
            )
        ]

    def __str__(self):
        return self.room_name


class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    time_range = models.CharField(max_length=20, editable=False)  # Prevent manual entry
    is_break = models.BooleanField(default=False)  # Optional: Mark breaks

    class Meta:
        ordering = ['start_time', 'end_time']  # Ensure proper slot ordering

    @property
    def is_morning(self):
        """Determine if slot is in the morning (before 12:00 PM)"""
        return self.start_time.hour < 12

    @property
    def is_afternoon(self):
        """Determine if slot is in the afternoon (12:00 PM or later)"""
        return self.start_time.hour >= 12

    def clean(self):
        """Validate time slot before saving."""
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

    def save(self, *args, **kwargs):
        """Auto-generate time_range before saving."""
        self.full_clean()  # Ensures clean() is called before saving

        # Format as 24-hour format (e.g., 10:30-11:30)
        self.time_range = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"

        super().save(*args, **kwargs)

    def __str__(self):
        """Return formatted time slot string."""
        break_label = " (Break)" if self.is_break else ""
        return f"{self.time_range}{break_label}"





class TimetableSlot(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    is_rescheduled = models.BooleanField(default=False)
    original_slot = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    teacher_assignment = models.ForeignKey(TeacherAssignment, on_delete=models.CASCADE,related_name='timetable_slots')  # Links to TeacherAssignment
    room = models.ForeignKey(Room, on_delete=models.CASCADE,related_name='timetable_slots')  # Room where the class is happening
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)  # Restrict to valid days
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)  # Specific time slot

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(room__isnull=False),
                name='room_required'
            )
        ]

    def __str__(self):
        return f"{self.teacher_assignment.subject.name} with {self.teacher_assignment.teacher.first_name} on {self.day_of_week} at {self.time_slot}"


# models.py
class RescheduleRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    original_slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE)
    new_slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE,
                                 related_name='reschedule_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()

# models.py
class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"