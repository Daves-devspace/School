from django.db import models
from django.db.models import Sum

from apps.students.models import Class, Student, Section
from apps.teachers.models import Teacher, Subject


# Create your models here.
class Term(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Term 1", "Term 2"
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "Term"
        verbose_name_plural = "Terms"
        ordering = ['start_date']
    def __str__(self):
        return f"{self.name} -{self.start_date}-{self.end_date}"

class TeacherSubject(models.Model):
    teacher = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_assigned = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['teacher', 'subject', 'grade_assigned']

    def __str__(self):
        return f"{self.teacher.username} - {self.subject} - {self.grade_assigned}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE, related_name="results",blank=True)
    term =models.ForeignKey(Term, on_delete=models.CASCADE, related_name="results")
    score = models.PositiveIntegerField()


    class Meta:
        unique_together = ['student', 'teacher_subject', 'term']

    def __str__(self):
        return f"{self.student.first_name} - {self.teacher_subject.subject.name} ({self.score})"


# class Performance(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="performances")
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="performances")
#     term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="performances")
#     marks = models.FloatField()
#     total_marks = models.FloatField()
#
#     @property
#     def percentage(self):
#         return (self.marks / self.total_marks) * 100
#
#     def __str__(self):
#         return f"{self.student} - {self.subject} ({self.term.name})"

class SubjectMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="studentperformances")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="subjectperformances")
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f'{self.student.first_name} - {self.subject.name} ({self.marks} marks)'

    class Meta:
       unique_together = ['student', 'subject']


class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards",default=1)
    date = models.DateField(auto_now_add=True)
    def total_marks(self):
        subject_marks = SubjectMark.objects.filter(student=self.student, term=self.term)
        return subject_marks.aggregate(Sum('marks'))['marks__sum']

    def student_rank(self):
        # Calculate rank based on total marks
        all_students = ReportCard.objects.filter(term=self.term).annotate(total=Sum('subjectmark__marks'))
        sorted_students = sorted(all_students, key=lambda x: x.total, reverse=True)
        return sorted_students.index(self) + 1

    def __str__(self):
        return f"{self.student.first_name} - {self.term.name}"



class Attendance(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="attendances")
    section = models.ForeignKey('students.Section', on_delete=models.CASCADE, related_name="attendances")  # Assuming Grade handles sections
    teacher = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # Assuming teachers are users
    date = models.DateField()
    is_present = models.BooleanField()
    term = models.ForeignKey('Term', on_delete=models.CASCADE, related_name="attendances")

    def __str__(self):
        return f"{self.student.first_name} - {self.date} ({'Present' if self.is_present else 'Absent'})"

    class Meta:
        unique_together = ('student', 'date')  # Prevent duplicate attendance for the same student on the same date
