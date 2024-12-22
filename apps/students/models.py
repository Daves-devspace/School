import os
import uuid

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField



# Create your models here.

def generate_unique_name(instance,filename):
    name = uuid.uuid4()
    full_file_name=f"{name}-{filename}"
    return os.path.join("student_images",full_file_name)


class Class(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Grade 1", "Grade 2"
    level = models.IntegerField()  # Used to determine progression (e.g., 1 for Grade 1, 2 for Grade 2)

    def __str__(self):
        return self.name

class Section(models.Model):
    name = models.CharField(max_length=50)  # e.g., "A", "B", "South", "North"
    grade = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="sections", null=True, blank=True)
    class_teacher = models.OneToOneField(
    'teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name="class_teacher_of"
    )  # One teacher can only be a class teacher for one section

    def __str__(self):
        return f"{self.grade} {self.name}"

class Parent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mobile = PhoneNumberField(region="KE", blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ('first_name', 'last_name', 'mobile')


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
    Class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, related_name="students")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    religion = models.CharField(max_length=10, choices=RELIGION_CHOICES)
    joining_date = models.DateField()
    admission_number = models.CharField(max_length=15, unique=True)
    student_image = models.ImageField(upload_to='students', blank=True, null=True)
    parent = models.ManyToManyField('Parent', through='StudentParent', related_name="students")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

    # def clean(self):
    #     # Ensure joining date is not in the future
    #     if self.joining_date > timezone.now().date():
    #         raise ValidationError("Joining date cannot be in the future.")


class StudentParent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=100, choices=[
        ("Father", "Father"),
        ("Mother", "Mother"),
        ("Guardian", "Guardian"),
        ("Other", "Other"),
    ])

    def __str__(self):
        return f"{self.parent} - {self.student} ({self.relationship})"





class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    year = models.IntegerField()
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







