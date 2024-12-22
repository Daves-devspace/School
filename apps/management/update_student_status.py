# student_management/management/commands/update_student_status.py
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.students.models import Student, Class


class Command(BaseCommand):
    help = 'Updates student grade and status after a year or upon graduation.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        # Get all students
        students = Student.objects.all()

        for student in students:
            # Change grade based on date (1 year progression)
            if student.grade:
                current_grade = student.grade
                next_grade = Class.objects.filter(level=current_grade.level + 1).first()  # Get the next grade
                if next_grade:
                    student.grade = next_grade
                    self.stdout.write(f"Student {student.first_name} {student.last_name} moved to {next_grade.name}")

            # Check graduation criteria (last grade in the system, or based on custom logic)
            if student.grade and student.grade.level >= 8:  # Assuming Grade 8 is the last grade (e.g., graduation)
                student.status = 'graduated'
                self.stdout.write(f"Student {student.first_name} {student.last_name} graduated")

            # Check if it's time for the student to move to the next grade based on joining date or current date
            if student.joining_date and today.year - student.joining_date.year >= 1:
                student.status = 'inactive'  # Mark as inactive after a year if not graduated

            # Save the changes
            student.save()
            self.stdout.write(f"Updated student {student.first_name} {student.last_name}'s status to {student.status}.")

