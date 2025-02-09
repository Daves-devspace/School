# tests/test_teacher_login.py
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

from apps.teachers.models import Teacher


class TeacherLoginTest(TestCase):
    def test_valid_teacher_login(self):
        # Create test user
        user = User.objects.create_user(username='TCH/TEST/00', password='testpass')
        group = Group.objects.create(name='Teacher')
        user.groups.add(group)
        Teacher.objects.create(user=user)

        # Test login flow
        response = self.client.post(reverse('login'), {
            'username': 'TCH/TEST/00',
            'password': 'testpass'
        }, follow=True)

        # Should redirect through home to teacher dashboard
        self.assertRedirects(response, '/teacher-dashboard/')
        self.assertContains(response, "Teacher Dashboard")