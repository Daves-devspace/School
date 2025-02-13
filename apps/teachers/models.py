import re
from datetime import date

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import ManyToManyField
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from phonenumber_field.modelfields import PhoneNumberField

from apps.management.models import Profile


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

class StaffNumberBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Look for a User with the provided staff_number
            user = User.objects.get(username=username)  # username is the staff_number here
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='teacher_profile')
    id_No = models.CharField(max_length=20, unique=True)
    staff_number = models.CharField(max_length=20, unique=True, blank=True)  # Allow auto-generation
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')]
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15,unique=True)
    qualification = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience")
    country = models.CharField(max_length=50)
    joining_date = models.DateField()
    subjects = models.ManyToManyField('schedules.Subject', related_name="teachers")
    is_headteacher = models.BooleanField(default=False)

    def clean(self):
        """ Ensure the staff number follows the correct format. """
        if self.staff_number and not re.match(r'^TCH/\d{3}/\d{2}$', self.staff_number):
            raise ValidationError('Invalid staff_number format. Expected format is TCH/001/25.')

    def save(self, *args, **kwargs):
        with transaction.atomic():  # Ensures all database actions are successful or rolled back
            if not self.user:
                # Create or retrieve associated user
                user, created = User.objects.get_or_create(
                    email=self.email,
                    defaults={'username': self.staff_number or self.generate_staff_number(),
                              'first_name': self.first_name,
                              'last_name': self.last_name}
                )
                self.user = user

            if not self.staff_number:
                self.staff_number = self.generate_staff_number()

            # Assign the staff_number as the username for the User
            self.user.username = self.staff_number
            self.user.save()

            # Validate before saving
            self.clean()
            super().save(*args, **kwargs)

    @staticmethod
    def generate_staff_number():
        """ Generate a unique staff number in the format TCH/001/25 """
        current_year = date.today().year
        year_suffix = str(current_year)[-2:]

        last_teacher = Teacher.objects.filter(staff_number__endswith=f"/{year_suffix}").order_by('-id').first()
        last_number = int(last_teacher.staff_number.split("/")[1]) if last_teacher else 0

        for _ in range(1000):  # Prevent infinite loops
            new_number = f"{last_number + 1:03d}"
            staff_number = f"TCH/{new_number}/{year_suffix}"
            if not Teacher.objects.filter(staff_number=staff_number).exists():
                return staff_number
            last_number += 1

        raise Exception("Unable to generate a unique staff number.")

    def get_title(self):
        """ Return Mr./Mrs. based on gender """
        return f"Mr. {self.last_name}" if self.gender == 'Male' else (f"Mrs. {self.last_name}" if self.gender == 'Female' else f"{self.first_name} {self.last_name}")

    def __str__(self):
        return f"{self.staff_number} - {self.first_name} {self.last_name}"

    class Meta:
        indexes = [models.Index(fields=['staff_number'])]

# # Teacher model remains the same
# class Teacher(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)  # Links to User model
#     id_No = models.CharField(max_length=20, unique=True)  # Represents the ID number
#     staff_number = models.CharField(max_length=20, unique=True, default='TCH/000/00')  # This will be used as username
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     gender = models.CharField(
#         max_length=10,
#         choices=[('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others')]
#     )
#     email = models.EmailField(unique=True)
#     phone = PhoneNumberField(region="KE", blank=False, null=False, default="0000000000")
#     qualification = models.CharField(max_length=100)
#     experience = models.PositiveIntegerField(help_text="Years of experience")
#     country = models.CharField(max_length=50)
#     joining_date = models.DateField()
#     subjects = models.ManyToManyField(
#         'schedules.Subject',
#         related_name="teachers"
#     )  # Link to Subject model
#     is_headteacher = models.BooleanField(default=False)
#
#     def save(self, *args, **kwargs):
#         if not self.staff_number:  # Generate staff number only if it doesn't exist
#             self.staff_number = self.generate_staff_number()
#         if self.user:
#             self.user.username = self.staff_number  # Assign the staff_number as the username for the User
#             self.user.save()
#         super().save(*args, **kwargs)
#
#     @staticmethod
#     def generate_staff_number():
#         """
#         Generate a unique staff number for teachers.
#         Format: TCH/001/25 (e.g., "TCH/{sequential_number}/{last_two_digits_of_year}")
#         """
#         current_year = date.today().year
#         year_suffix = str(current_year)[-2:]
#
#         # Fetch the last registered teacher
#         last_teacher = Teacher.objects.order_by('-id').first()
#
#         if last_teacher and last_teacher.staff_number:
#             last_number = int(last_teacher.staff_number.split("/")[1])  # Get the middle number
#         else:
#             last_number = 0  # Default to 0 if no teacher exists
#
#         new_number = f"{last_number + 1:03d}"  # Increment and format as 3 digits
#         return f"TCH/{new_number}/{year_suffix}"
#
#     def __str__(self):
#         return f"{self.staff_number} - {self.full_name}"


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey('schedules.Subject', on_delete=models.CASCADE)
    grade_section = models.ForeignKey(
        "students.GradeSection",
        on_delete=models.CASCADE,
        related_name="teacher_assignments"  # Add related_name here
    )
    assigned_date = models.DateField(auto_now=True)
#ensure no duplicate assignments
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject', 'grade_section'],
                name='unique_subject_in_grade_section'
            )
        ]
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
