from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import ManyToManyField
from phonenumber_field.modelfields import PhoneNumberField




# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Mathematics", "English", etc.
    grade = models.ForeignKey("students.Class", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

# Create a TeachingAssignment model to break the circular dependency
class TeachingAssignment(models.Model):
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignments')
    # class_assigned = models.ForeignKey('students.Class', on_delete=models.CASCADE, related_name='assignments')
    section = models.ForeignKey('students.Section', on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    assigned_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("teacher", "subject", "section")  # Prevent duplicate assignments

    def __str__(self):
        return f"{self.teacher.full_name} - {self.subject.name}  - {self.section.name}"



class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)  # Links to Django's User model
    teacher_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=30)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others'),
    ])
    phone_no = PhoneNumberField(region="KE", blank=True, null=True)
    email = models.EmailField(unique=True)
    qualification = models.CharField(max_length=100)
    experience = models.PositiveIntegerField(help_text="Years of experience")
    address = models.TextField()
    country = models.CharField(max_length=50)
    joining_date = models.DateTimeField()
    subjects = models.ManyToManyField(Subject, related_name='teachers')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}"  # Display class name along with teacher's name






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
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'department', 'role')  # Prevent duplicate assignments

    def clean(self):
        # Ensure teacher belongs to the department
        if self.role.name == "Dean" and self.department.hod != self.teacher:
            raise ValidationError(f"{self.teacher} is not the HOD for {self.department}.")

    def __str__(self):
        return f"{self.teacher.full_name} - {self.role.name} - ({self.department.name})"







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