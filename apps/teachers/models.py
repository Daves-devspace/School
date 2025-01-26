from datetime import date

from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import ManyToManyField
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from phonenumber_field.modelfields import PhoneNumberField

from apps.management.models import  Profile


# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# class Subject(models.Model):
#     name = models.CharField(max_length=100)  # e.g., "Mathematics", "English", etc.
#     grade = models.ForeignKey("students.Grade", on_delete=models.CASCADE)
#
#     def __str__(self):
#         return self.name









# Teacher model remains the same
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)  # Links to User model
    id_No = models.CharField(max_length=20, unique=True)  # Represents the ID number
    staff_number = models.CharField(max_length=20, unique=True, default='TCH/000/00')
    full_name = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')]
    )
    email = models.EmailField(unique=True)
    qualification = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience")
    country = models.CharField(max_length=50)
    joining_date = models.DateTimeField()
    subjects = models.ManyToManyField(
        'schedules.Subject',
        related_name="teachers"
    )  # Link to Subject model
    is_headteacher = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.staff_number:  # Generate staff number only if it doesn't exist
            self.staff_number = self.generate_staff_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_staff_number():
        """
        Generate a unique staff number for teachers.
        Format: TCH/001/25 (e.g., "TCH/{sequential_number}/{last_two_digits_of_year}")
        """
        current_year = date.today().year
        year_suffix = str(current_year)[-2:]

        # Fetch the last registered teacher
        last_teacher = Teacher.objects.order_by('-id').first()

        if last_teacher and last_teacher.staff_number:
            last_number = int(last_teacher.staff_number.split("/")[1])  # Get the middle number
        else:
            last_number = 0  # Default to 0 if no teacher exists

        new_number = f"{last_number + 1:03d}"  # Increment and format as 3 digits
        return f"TCH/{new_number}/{year_suffix}"

    def get_display_name(self):
        """
        Returns a shortened display name for the teacher using their surname's first letter.
        Example: 'Mr. K' for a male teacher with the last name starting with K.
        """
        if self.full_name:
            # Split full name to extract the last name
            name_parts = self.full_name.split()
            last_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
            prefix = "Mr." if self.gender == "Male" else "Ms." if self.gender == "Female" else "Mx."
            return f"{prefix} {last_name[0].upper()}"  # Use the first letter of the last name, uppercase
        return "Unknown"

    def __str__(self):
        role = "Headteacher" if self.is_headteacher else "Teacher"
        return f"{self.user.username if self.user else self.id_No} - {role}"






class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey('schedules.Subject', on_delete=models.CASCADE)
    grade_section = models.ForeignKey(
        "students.GradeSection",
        on_delete=models.CASCADE,
        related_name="teacher_assignments"  # Add related_name here
    )
    assigned_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['teacher', 'subject', 'grade_section']  # Ensure no duplicate assignments
        ordering = ['grade_section__grade', 'subject__name']

    def __str__(self):
        return f"{self.teacher} assigned to {self.subject.name} ({self.grade_section})"



class Department(models.Model):
    name = models.CharField(max_length=100)
    hod = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="head_of_department"
    )
    teachers = models.ManyToManyField(Teacher, through='TeacherRole', related_name='teaching_departments')


    def clean(self):
        if self.hod and not Teacher.objects.filter(pk=self.hod.pk).exists():
            raise ValidationError(f"{self.hod} is not a valid teacher.")

    def __str__(self):
        return self.name



class TeacherRole(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=[('HOD', 'Head of Department'), ('Teacher', 'Teacher')])

    class Meta:
        unique_together = ['teacher', 'department']  # Ensure each teacher can only have one role per department

    def __str__(self):
        return f'{self.teacher.full_name} - {self.role}'




#
# class Teacher(models.Model):
#     user_name = models.CharField(max_length=20)
#     full_name = models.CharField(max_length=30)
#     phone_no = PhoneNumberField(region="KE", blank=True, null=True)
#     subjects = ManyToManyField(Subject, related_name='teachers')
#     assigned_class = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
#    # assigned_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
#     department = models.ForeignKey(Department, related_name="teachers", on_delete=models.SET_NULL, null=True, blank=True)
#     joining_date = models.DateTimeField()
#
#
#     class Meta:
#         db_table = 'teachers'
#
#     def __str__(self):
#         return  f"{self.user_name} {self.phone_no}"
#
#     def get_subjects(self):
#         return ", ".join([subject.name for subject in self.subjects.all()])