import json
from datetime import date, datetime

import logging
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView

from django.db.models import Sum
from django.db.models.functions.datetime import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from School import settings
from apps.Manage.forms import CustomSignupForm
from apps.accounts.models import FeePayment
from apps.management.models import Term, SubjectMark, Attendance
from apps.students.models import Student, GradeSection
from apps.students.utils import MobileSasaAPI
from apps.students.views import get_current_term
from apps.teachers.models import Teacher, Department
from apps.website.forms import AppointmentForm
from apps.website.models import Appointment, AppointmentReply

from .forms import SmsProviderTokenForm
from .models import SmsProviderToken


# Create your views here.


@login_required
def home(request):
    # Get the user's groups
    user_groups = request.user.groups.values_list('name', flat=True)

    # Redirect to the appropriate dashboard based on user role
    if 'Director' in user_groups:
        return redirect('director_dashboard')  # URL name for the Admin dashboard
    elif 'Teacher' in user_groups:
        return redirect('teacher_dashboard')  # URL name for the Teacher dashboard
    elif 'Head Teacher' in user_groups:
        return redirect('student_dashboard')  # URL name for the Student dashboard
    else:
        return redirect('director_dashboard')  # URL name for a fallback or guest dashboard


def login_user(request):
    if request.method == 'GET':
        return redirect('login_form')

    elif request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)  # Log in the user

            # JWT token generation
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Store tokens in cookies
                secure_cookie = not settings.DEBUG  # Secure cookies in production
                response = redirect('home')
                response.set_cookie('access_token', access_token, httponly=True, secure=secure_cookie,
                                    samesite='Strict')
                response.set_cookie('refresh_token', refresh_token, httponly=True, secure=secure_cookie,
                                    samesite='Strict')
            except Exception as e:
                messages.error(request, f"Token generation error: {e}")
                return redirect('login')

            messages.success(request, 'You are logged in!')
            return response

        # Authentication failed
        messages.warning(request, 'Invalid username or password')
        return redirect('login')


@api_view(['POST'])
def protected_view(request):
    access_token = request.COOKIES.get('access_token')
    if not access_token:
        return Response({'error': 'No access token provided.'}, status=401)

    try:
        token = AccessToken(access_token)
        return Response({'message': 'Access granted!'}, status=200)
    except TokenError as e:
        return Response({'error': str(e)}, status=401)


def login_form(request):
    # Check if there are any messages to display (e.g., after logout)
    return render(request, 'Home/login_form.html', {'messages': messages.get_messages(request)})


logger = logging.getLogger(__name__)


@login_required
def director_dashboard(request):
    try:
        current_year = date.today().year
        current_term = get_current_term()
        term_year = current_term.start_date.year if current_term else current_year

        # Aggregate data
        total_revenue = FeePayment.objects.filter(date__year=current_year).aggregate(
            total=Sum('amount')
        )['total'] or 0
        total_students = Student.objects.filter(status="active").count()
        total_teachers = Teacher.objects.count()
        total_departments = Department.objects.count()

        logger.info(f"Revenue: {total_revenue}, Students: {total_students}, Teachers: {total_teachers}")

        # Top students data
        # top_students_data = []
        # grade_sections = GradeSection.objects.all()
        # for section in grade_sections:
        #     # Get top 3 students in this grade section
        #     top_3_students = (SubjectMark.objects.filter(student__grade=section)
        #                       .values('student', 'student__first_name', 'student__last_name', 'student__admission_number')
        #                       .annotate(total_marks=Sum('marks'))
        #                       .order_by('-total_marks')[:3])
        #
        #     for student_data in top_3_students:
        #         subject_mark = SubjectMark.objects.filter(student=student_data['student']).first()
        #         term = subject_mark.term.name if subject_mark and subject_mark.term else "N/A"
        #         exam_type = subject_mark.exam_type.name if subject_mark and subject_mark.exam_type else "N/A"
        #         year = term_year
        #
        #         top_students_data.append({
        #             'student_name': f"{student_data['student__first_name']} {student_data['student__last_name']}",
        #             'admission_number': student_data['student__admission_number'],
        #             'total_marks': student_data['total_marks'],
        #             'class': section.grade,
        #             'term': term,
        #             'exam_type': exam_type,
        #             'year': year,
        #         })

        return render(request, 'Home/Admin/index.html', {
            "total_revenue": total_revenue,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_departments": total_departments,
            'current_year': current_year,
            # 'top_students_data': top_students_data,
        })
    except Exception as e:
        import traceback
        logger.error(f"Error in director_dashboard: {e}\n{traceback.format_exc()}")
        return render(request, 'Manage/errors/500.html', {"error_message": str(e)})


@login_required
def teacher_dashboard(request):
    # Check if the user belongs to the "Teacher" group
    if not request.user.groups.filter(name="Teacher").exists():
        return redirect("logout")

    # Retrieve the corresponding Teacher instance for the logged-in user
    teacher = get_object_or_404(Teacher, user=request.user)
    # Fetch the grade sections assigned to this teacher
    grade_sections = GradeSection.objects.filter(class_teacher=teacher)

    current_term = get_current_term()

    # Render the teacher dashboard template with attendance data
    return render(request, 'Home/Teacher/teacher-dashboard.html', {
        'grade_sections': grade_sections,
        'current_term': current_term,

    })


def logout_user(request):
    # Log out the user
    logout(request)

    # Clear any authentication tokens stored in cookies
    response = redirect('login_form')  # Redirect to the login page
    response.delete_cookie('access_token')  # Clear the access token
    response.delete_cookie('refresh_token')  # Clear the refresh token

    # Add a success message
    messages.success(request, 'You have been logged out successfully!')

    return response


def head_teacher_dashboard(request):
    return None


def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            # Assign user to the selected group
            role = form.cleaned_data['role']
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)

            # Log the user in and redirect based on their role
            login(request, user)
            if role == 'Teacher':
                return redirect('teacher_dashboard')  # Replace with the actual URL name
            elif role == 'Head Teacher':
                return redirect('head_teacher_dashboard')  # Replace with the actual URL name
            elif role == 'Director':
                return redirect('director_dashboard')  # Replace with the actual URL name
    else:
        form = CustomSignupForm()
    return render(request, 'Home/signup.html', {'form': form})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password-reset-done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password-reset-confirm.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password-reset-complete.html'


# def login_form(request):


def website_page(request):
    form = AppointmentForm()
    return render(request, 'Home/website/index.html', {'form': form})


@login_required
# View to render the inbox
def inbox_view(request):
    successful_replies = []
    failed_replies = []
    appointments = Appointment.objects.all().order_by('-created_at')

    # Example of fetching replies related to appointments
    for appointment in appointments:
        # Assuming `appointment` has an associated reply with a status field
        if appointment.reply_status == 'success':
            successful_replies.append({
                'phone': appointment.phone,  # Adjust field name accordingly
                'message': appointment.reply_message  # Adjust field name accordingly
            })
        else:
            failed_replies.append({
                'phone': appointment.phone,  # Adjust field name accordingly
                'reason': appointment.reply_failure_reason  # Adjust field name accordingly
            })

    return render(request, 'Manage/inbox.html', {
        'appointments': appointments,
        'successful_replies': successful_replies,
        'failed_replies': failed_replies
    })


# View to fetch appointment details as JSON
@login_required
def get_appointment_details(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return JsonResponse({
        "guardian": appointment.guardian_name,
        "child": appointment.child_name,
        "date": appointment.date.strftime("%Y-%m-%d"),
        "time": appointment.time.strftime("%I:%M %p"),
        "phone": appointment.phone,
        "email": appointment.email,
        "message": appointment.message
    })


# View to handle reply to an appointment
@csrf_exempt
@login_required
def reply_appointment(request, appointment_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message")

            # Validate the message content
            if not message:
                return JsonResponse({"status": "error", "message": "Message cannot be empty."})

            # Get the appointment object
            appointment = get_object_or_404(Appointment, id=appointment_id)

            # Store the reply in the database
            AppointmentReply.objects.create(appointment=appointment, teacher=request.user, message=message)

            # Instantiate the MobileSasaAPI class to send SMS
            sms_provider = MobileSasaAPI()

            # Send the SMS using the MobileSasaAPI instance
            phone = appointment.phone  # Get the phone number from the appointment
            sms_response = sms_provider.send_single_sms(message, phone)  # Send SMS to the guardian

            # Check if the SMS response is a dictionary and contains a "status" key
            if isinstance(sms_response, dict) and sms_response.get("status"):
                # SMS sent successfully
                appointment.reply_status = 'success'
                appointment.reply_message = message
                appointment.save()
                return JsonResponse({"status": "success", "message": "Reply sent via SMS!"})
            else:
                # Handle case where sms_response is not a dictionary
                error_message = sms_response if isinstance(sms_response, str) else sms_response.get("message",
                                                                                                    "Failed to send SMS.")
                return JsonResponse({"status": "error", "message": error_message})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format in request."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"})




class SettingsView(View):
    template_name = 'Manage/settings.html'  # Your settings page template

    def get(self, request):
        """Handles GET requests and renders the settings page."""
        form = SmsProviderTokenForm()  # Initialize the form
        context = {
            'form': form,
            # Add other settings-related context here if needed
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handles POST requests to update the SMS token."""
        form = SmsProviderTokenForm(request.POST)
        if form.is_valid():
            # Extract data from the form
            api_token = form.cleaned_data['api_token']
            sender_id = form.cleaned_data['sender_id']

            # Update or create the SmsProviderToken (only one record exists with id=1)
            SmsProviderToken.objects.update_or_create(
                id=1,  # Ensures only one record is updated or created
                defaults={'api_token': api_token, 'sender_id': sender_id}
            )

            # After saving the data, redirect back to the settings page
            return redirect('settings_page')  # Redirect back to settings page after saving
        else:
            # In case the form is invalid, return the form with errors
            context = {
                'form': form,  # Keep the form with errors
            }
            return render(request, self.template_name, context)

