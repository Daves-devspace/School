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
    #get the most recent before the current term
    def get_previous_term(self):
        return Term.objects.filter(start_date__lt=self.start_date).order_by('-start_date').first()
    #next after current
    def get_next_term(self):
        return Term.objects.filter(start_date__gt=self.start_date).order_by('start_date').first()




class TeacherSubject(models.Model):
    teacher = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade_assigned = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['teacher', 'subject', 'grade_assigned']

    def __str__(self):
        return f"{self.teacher.username} - {self.subject} - {self.grade_assigned}"

class ExamType(models.Model):
    name = models.CharField(max_length=50)  # E.g., "Opener", "Mid-Term", "End-Term"
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exam_types')
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'term')  # Ensure a term can't have duplicate exam types

    def __str__(self):
        return f"{self.name} - {self.term}"


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
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey('teachers.Subject', on_delete=models.CASCADE)
    term = models.ForeignKey('Term', on_delete=models.CASCADE)
    exam_type = models.ForeignKey('ExamType', on_delete=models.CASCADE)  # Link to ExamType
    marks = models.FloatField()

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam_type} ({self.marks})"



class ReportCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="report_cards")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="report_cards",default=1)
    date = models.DateField(auto_now_add=True)

    def total_marks(self):
        subject_marks = SubjectMark.objects.filter(student=self.student, term=self.term)
        total = subject_marks.aggregate(Sum('marks'))['marks__sum'] or 0  # Default to 0 if None
        return total

    def student_rank(self):
        # Annotate each report card with the total marks
        all_students = ReportCard.objects.filter(term=self.term).annotate(total_marks=Sum('subjectmark__marks'))

        # Sort by total marks in descending order
        sorted_students = sorted(all_students, key=lambda x: x.total_marks, reverse=True)

        # Get the rank by index
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
