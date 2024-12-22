from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from apps.students.models import Student, Class


@shared_task
def update_student_status():
    today = timezone.now().date()

    # Get all students
    students = Student.objects.all()

    for student in students:
        # Update grade based on the level progression (assuming level 1 -> 2, 2 -> 3, etc.)
        if student.grade:
            current_grade = student.grade
            next_grade = Class.objects.filter(level=current_grade.level + 1).first()  # Get the next grade
            if next_grade:
                student.grade = next_grade
                student.save()
                print(f"Student {student.first_name} {student.last_name} moved to {next_grade.name}")

        # Graduation check (assuming level 8 or greater is graduation)
        if student.grade and student.grade.level >= 8:  # Assuming Grade 8 is the last grade
            student.status = 'graduated'
            student.save()
            print(f"Student {student.first_name} {student.last_name} graduated.")

        # Mark as inactive after a year (if the joining date is over a year ago and not graduated)
        if student.joining_date and (today - student.joining_date).days >= 365:
            if student.status != 'graduated':  # Don't mark as inactive if the student is already graduated
                student.status = 'inactive'
                student.save()
                print(f"Student {student.first_name} {student.last_name}'s status set to inactive.")

