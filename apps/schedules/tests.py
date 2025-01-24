from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from apps.schedules.models import Subject, Room, TimeSlot, TimetableSlot
from apps.students.models import GradeSection
from apps.teachers.models import Teacher, TeacherAssignment


class TimetableTestCase(TestCase):

    def setUp(self):
        # Create a user for authentication (if required)
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Create some mock data for GradeSection, Teacher, Subject, Room, TimeSlot, and TeacherAssignment
        self.grade_section_1 = GradeSection.objects.create(grade_id=1, name='Grade 1A')
        self.grade_section_2 = GradeSection.objects.create(grade_id=2, name='Grade 2A')

        self.subject = Subject.objects.create(name='Math')
        self.teacher = Teacher.objects.create(name='John Doe')

        self.room = Room.objects.create(name='Room 101')
        self.time_slot = TimeSlot.objects.create(start_time='08:00', end_time='09:00', day_of_week=1)  # Monday

        # Create TeacherAssignments for GradeSections
        self.teacher_assignment_1 = TeacherAssignment.objects.create(
            grade_section=self.grade_section_1,
            teacher=self.teacher,
            subject=self.subject
        )
        self.teacher_assignment_2 = TeacherAssignment.objects.create(
            grade_section=self.grade_section_2,
            teacher=self.teacher,
            subject=self.subject
        )

        # Create TimetableSlots associated with TeacherAssignments
        self.timetable_slot_1 = TimetableSlot.objects.create(
            teacher_assignment=self.teacher_assignment_1,
            room=self.room,
            time_slot=self.time_slot
        )
        self.timetable_slot_2 = TimetableSlot.objects.create(
            teacher_assignment=self.teacher_assignment_2,
            room=self.room,
            time_slot=self.time_slot
        )

    def test_generate_timetable_for_all(self):
        # Test that the timetable generation view works correctly
        url = reverse('generate_timetable_for_all')  # Update with the actual URL name
        response = self.client.get(url)

        # Check the response status
        self.assertEqual(response.status_code, 200)

        # Check if timetable data is included in the response context
        self.assertIn('all_timetables', response.context)

        # Verify that the timetable slots are rendered properly in the response
        all_timetables = response.context['all_timetables']
        self.assertEqual(len(all_timetables), 2)  # Should have 2 timetables in the context

        # Check that the timetable slots are in the expected order
        self.assertEqual(all_timetables[0]['grade_section'].name, 'Grade 1A')
        self.assertEqual(all_timetables[1]['grade_section'].name, 'Grade 2A')

        # Ensure that each timetable has the correct teacher assignment
        self.assertEqual(all_timetables[0]['timetable_slots'][0].teacher_assignment.teacher.name, 'John Doe')
        self.assertEqual(all_timetables[1]['timetable_slots'][0].teacher_assignment.teacher.name, 'John Doe')

        # You can also test more specific data here depending on the structure of the template
        # For example, check for the presence of HTML elements that contain the timetable info
        self.assertContains(response, 'Grade 1A')
        self.assertContains(response, 'Grade 2A')
        self.assertContains(response, 'John Doe')
