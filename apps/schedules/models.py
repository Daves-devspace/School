from django.db import models


from apps.teachers.models import Teacher, TeacherAssignment


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

    # Optional Foreign Key if the subject is taught only in one specific grade
    single_grade = models.ForeignKey(
        'students.Grade', null=True, blank=True, on_delete=models.SET_NULL, related_name='single_subjects_schedules'
    )

    # Department and special room details
    department = models.CharField(max_length=100, blank=True, null=True)
    requires_special_room = models.BooleanField(
        default=False  # Whether the subject needs a special room (e.g., computer lab)
    )
    special_room = models.ForeignKey(
        'Room', null=True, blank=True, on_delete=models.SET_NULL, related_name='subject_special_rooms'
    )  # Reference to the special room if required

    def __str__(self):
        if self.single_grade:
            return f"{self.name} (Only in {self.single_grade.name})"
        grades_list = ", ".join(grade.name for grade in self.grade.all())
        return f"{self.name} ({grades_list})" if grades_list else self.name






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

    def __str__(self):
        return self.room_name



class TimeSlot(models.Model):
    start_time = models.TimeField()  # Start time of the lesson
    end_time = models.TimeField()    # End time of the lesson
    time_range = models.CharField(max_length=20)  # e.g. "09:00-10:00", "11:20-12:00"

    def save(self, *args, **kwargs):
        # Auto-generate the time_range based on start_time and end_time
        self.time_range = f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        super(TimeSlot, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.start_time} to {self.end_time}"



#
# class TeacherAssignment(models.Model):
#     teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,related_name='teacherassignments_schedules')
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
#     grade_section = models.ForeignKey("students.GradeSection", on_delete=models.CASCADE,related_name='teacherassignments_schedules')
#     assigned_date = models.DateField(auto_now_add=True)
#
#     class Meta:
#         unique_together = ['teacher', 'subject', 'grade_section']  # Ensure no duplicate assignments
#         ordering = ['grade_section__grade', 'subject__name']
#
#     def __str__(self):
#         return f"{self.teacher} assigned to {self.subject.name} ({self.grade_section})"





# Model for Timetable Slot (A specific schedule for a course, instructor, and room)
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

    teacher_assignment = models.ForeignKey(TeacherAssignment, on_delete=models.CASCADE)  # Links to TeacherAssignment
    room = models.ForeignKey(Room, on_delete=models.CASCADE)  # Room where the class is happening
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)  # Restrict to valid days
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)  # Specific time slot

    def __str__(self):
        return f"{self.teacher_assignment.subject.name} with {self.teacher_assignment.teacher.full_name} on {self.day_of_week} at {self.time_slot}"


