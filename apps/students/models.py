import os
import uuid
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField

from apps.schedules.models import Room
from apps.teachers.models import Teacher


# Create your models here.

def generate_unique_name(instance,filename):
    name = uuid.uuid4()
    full_file_name=f"{name}-{filename}"
    return os.path.join("student_images",full_file_name)

class Grade(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Grade 1", "Grade 2"
    level = models.IntegerField(unique=True)  # Ensure progression levels are unique

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['level']


class Section(models.Model):
    name = models.CharField(max_length=50)  # e.g., "A", "B", "South", "North"

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['name']



class GradeSection(models.Model):
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name="grade_sections"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="section_grade_sections"
    )

    class_teacher = models.OneToOneField(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_teacher_of",
    )  # A teacher can only teach one section

    class Meta:
        unique_together = ("grade", "section")
        ordering = ["grade", "grade__level", "section__name"]

    def __str__(self):
        return f"{self.grade.name} {self.section.name}"

    def save(self, *args, **kwargs):
        # Save the GradeSection instance first
        super().save(*args, **kwargs)

        # Ensure grade and section names are valid
        grade_name = self.grade.name.strip() if self.grade.name else "Grade"
        section_name = self.section.name.strip() if self.section.name else "Section"

        # Generate a room name (e.g., "G1A" for Grade 1, Section A)
        room_name = f"{grade_name[0].upper()}{self.grade.level}{section_name[0].upper()}"

        # Check if a room with this name already exists
        if not Room.objects.filter(room_name=room_name).exists():
            # Create a new Room with the generated name
            Room.objects.create(
                room_name=room_name,
                is_special=False  # Default to non-special rooms
            )


class Parent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ('first_name', 'last_name', 'mobile')
        verbose_name_plural = "Parents"  # Use proper pluralization in admin


class Student(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Graduated", "Graduated"),
    ]
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female")]
    RELIGION_CHOICES = [("Christian", "Christian"), ("Muslim", "Muslim"), ("Other", "Other")]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    grade = models.ForeignKey(
        GradeSection, on_delete=models.SET_NULL, null=True, related_name="students"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    sponsored = models.BooleanField(default=False)  # Track if the student is sponsored
    religion = models.CharField(max_length=10, choices=RELIGION_CHOICES)
    joining_date = models.DateField()
    admission_number = models.CharField(max_length=15, unique=True)
    student_image = models.ImageField(upload_to='students', blank=True, null=True)

    documents = models.FileField(upload_to='student_documents/', blank=True, null=True,
                                 help_text="Upload student-related documents")

    parent = models.ManyToManyField(
        Parent, through='StudentParent', related_name="students"
    )
    last_promoted = models.DateTimeField(null=True, blank=True)  # Track last promotion date

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

    def save(self, *args, **kwargs):
        if not self.admission_number:  # Only generate if it doesn't already exist
            self.admission_number = self.generate_admission_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_admission_number():
        """
        Generate a unique admission number for each student.
        Format: MFS/{sequential_number}/{year_last_two_digits}
        """
        current_year = date.today().year  # Get the current year (e.g., 2025)
        year_suffix = str(current_year)[-2:]  # Extract the last two digits of the year (e.g., 25)

        # Fetch the last registered student
        last_student = Student.objects.order_by('-id').first()

        # Extract the sequential number
        if last_student and last_student.admission_number:
            last_number = int(last_student.admission_number.split("/")[1])  # Get the middle part (001)
        else:
            last_number = 0  # Default to 0 if no previous student exists

        # Increment the number and format it as a 3-digit number
        new_number = f"{last_number + 1:03d}"

        # Return the formatted admission number
        return f"MFS-{new_number}-{year_suffix}"

    def clean(self):
        # Ensure joining date is not in the future
        if self.joining_date > now().date():
            raise ValidationError("Joining date cannot be in the future.")
        # Ensure date of birth is not in the future
        if self.date_of_birth >= now().date():
            raise ValidationError("Date of birth must be in the past.")

    def promote(self):
        """Promote student to the next grade section or mark as graduated."""
        current_grade_level = self.grade.grade.level
        max_grade_level = Grade.objects.aggregate(max_level=Max('level'))['max_level']

        if current_grade_level == max_grade_level:
            # If in the highest grade, mark as graduated
            self.status = "Graduated"
            self.last_promoted = now()
            self.save()
            return "Graduated"

        # Fetch the next grade and grade section
        next_grade = Grade.objects.filter(level=current_grade_level + 1).first()
        if not next_grade:
            return "Error: Next grade not found."

        next_grade_section = GradeSection.objects.filter(
            grade=next_grade, section=self.grade.section
        ).first()

        if not next_grade_section:
            return f"Error: No section available for Grade {next_grade.name} and Section {self.grade.section.name}."

        # Promote student
        self.grade = next_grade_section
        self.last_promoted = now()
        self.save()
        return "Promoted"


class StudentParent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    relationship = models.CharField(
        max_length=100,
        choices=[
            ("Father", "Father"),
            ("Mother", "Mother"),
            ("Guardian", "Guardian"),
            ("Other", "Other"),
        ],
    )

    def __str__(self):
        return f"{self.parent} - {self.student} ({self.relationship})"

    class Meta:
        unique_together = ('student', 'parent')

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    year =  models.DateField()
    subject = models.CharField(max_length=100)
    isbn = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.title}-{self.isbn}"

    verbose_name = 'Book'
    verbose_name_plural = 'Books'
    ordering = ['isbn']
    db_table = 'books'


class Transaction(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transactions')
    status = models.CharField(max_length=20)
    expected_return_date = models.DateField()
    return_date = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book}-{self.student}"

    @property
    def overdue_days(self):
        if self.return_date and self.expected_return_date and self.return_date > self.expected_return_date:
            return (self.return_date - self.expected_return_date).days
        return 0

    @property
    def total_fine(self):
        return self.overdue_days * 10  # Assuming fine rate is 10 per day

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        db_table = 'transactions'


class Payment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    code = models.CharField(max_length=30, null=True)
    amount = models.IntegerField()
    status = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        db_table = 'payments'

    def __str__(self):
        return f"{self.transaction}-{self.code} -{self.amount}"







