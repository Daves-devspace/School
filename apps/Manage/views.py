import json
from datetime import date
from django.utils import timezone

import logging
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView

from django.db.models import Sum
from django.db.models.functions.datetime import TruncMonth
from django.http import JsonResponse, request
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from School import settings
from apps.Manage.forms import CustomSignupForm, UserCreateForm
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


from django.contrib.auth.models import Group

from ..schedules.models import TimetableSlot

logger = logging.getLogger(__name__)


def get_user_role_redirect(user):
    user_groups = set(user.groups.values_list('name', flat=True))
    role_redirect_map = {
        'Director': 'director_dashboard',
        'Teacher': 'teacher_dashboard',
        'Head Teacher': 'head_teacher_dashboard',
    }

    for role, url_name in role_redirect_map.items():
        if role in user_groups:
            return url_name
    return None


@require_http_methods(["GET"])
@login_required
def home(request):
    logger.debug(f"Home view accessed by {request.user}")

    if request.user.is_superuser:
        logger.debug("Redirecting superuser to director dashboard")
        return redirect('director_dashboard')

    if redirect_url := get_user_role_redirect(request.user):
        logger.debug(f"Redirecting {request.user} to {redirect_url}")
        return redirect(redirect_url)

    messages.warning(request, "Your account has no assigned role")
    return redirect('logout')


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            logger.debug(f"User {user} logged in successfully")
            messages.success(request, 'Welcome back!')
            return redirect('home')

        messages.error(request, 'Invalid credentials')
        return redirect('login')

    # Show login form for GET requests
    return render(request, 'Home/login_form.html')


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            data = response.data
            response.set_cookie(
                key="access_token",
                value=data["access"],
                httponly=True,  # Prevents JavaScript from accessing it
                secure=True,  # Set to True in production (HTTPS required)
                samesite="Lax",  # Helps with CSRF protection
            )
            response.set_cookie(
                key="refresh_token",
                value=data["refresh"],
                httponly=True,
                secure=True,
                samesite="Lax",
            )

        return response

@api_view(["POST"])

def refresh_token_view(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"error": "No refresh token provided."}, status=401)

    try:
        new_access_token = str(RefreshToken(refresh_token).access_token)
        response = Response({"message": "Token refreshed successfully."})
        response.set_cookie("access_token", new_access_token, httponly=True, secure=True, samesite="Lax")
        return response
    except Exception as e:
        return Response({"error": str(e)}, status=401)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Requires session authentication
def protected_view(request):
    access_token_str = request.COOKIES.get('access_token')

    if not access_token_str:
        return Response({'error': 'No access token provided.'}, status=401)

    try:
        # Convert string into an AccessToken object (if valid)
        access_token = AccessToken(access_token_str)

        # Extract user info from the token
        user_id = access_token.get('user_id', None)

        return Response({'message': 'Access granted!', 'user_id': user_id}, status=200)

    except TokenError as e:
        return Response({'error': str(e)}, status=401)

@api_view(["GET"])
@ensure_csrf_cookie
def get_csrf_token(request):
    """Returns CSRF token for frontend"""
    return JsonResponse({"message": "CSRF token set"}, status=200)

def login_form(request):
    # Check if there are any messages to display (e.g., after logout)
    return render(request, 'Home/login_form.html', {'messages': messages.get_messages(request)})


@login_required
def director_dashboard(request):
    try:
        current_year = date.today().year
        current_term = get_current_term()
        term_year = current_year if not current_term else (current_term.start_date.year if current_term.start_date else current_year)

        # Aggregate data
        total_revenue = FeePayment.objects.filter(date__year=current_year).aggregate(
            total=Sum('amount')
        )['total'] or 0
        total_students = Student.objects.filter(status="Active").count()
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




@method_decorator(login_required, name='dispatch')
class teacher_dashboard(View):
    def get(self, request):
        logger.debug(f"User groups: {list(request.user.groups.values_list('name', flat=True))}")
        logger.debug(f"Teacher profile exists: {hasattr(request.user, 'teacher_profile')}")

        try:
            teacher = getattr(request.user, 'teacher_profile', None)
            if teacher is None:
                raise Teacher.DoesNotExist  # Trigger error handling
        except Teacher.DoesNotExist:
            logger.error(f"Teacher profile missing for user {request.user}")
            messages.error(request, "No teacher profile found. Contact admin.")
            return redirect('home')

        current_datetime = timezone.now()
        current_day = current_datetime.strftime('%A')

        # Fetch lessons for today
        upcoming_slots = TimetableSlot.objects.filter(
            teacher_assignment__teacher=teacher,
            day_of_week=current_day
        ).select_related('time_slot', 'room', 'teacher_assignment__grade_section').order_by('time_slot__start_time')

        # Fetch full weekly schedule
        weekly_schedule = TimetableSlot.objects.filter(
            teacher_assignment__teacher=teacher
        ).select_related('time_slot', 'room', 'teacher_assignment__grade_section').order_by('day_of_week', 'time_slot__start_time')

        # Get class management data
        grade_sections = GradeSection.objects.filter(class_teacher=teacher)
        current_term = get_current_term()

        # Notification system
        notifications = request.user.notifications.all()[:10]
        unread_count = request.user.notifications.filter(read=False).count()

        context = {
            'upcoming_slots': upcoming_slots,
            'weekly_schedule': weekly_schedule,  # Add full weekly schedule to context
            'current_day': current_day,
            'grade_sections': grade_sections,
            'current_term': current_term,
            'notifications': notifications,
            'unread_count': unread_count,
            'teacher': teacher
        }

        return render(request, 'Home/Teacher/teacher-dashboard.html', context)

def logout_user(request):
    # Invalidate the JWT token (log out on front-end as well)
    response = redirect('login')
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    logout(request)  # Django logout to clear session
    messages.success(request, "You have been logged out.")
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
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        messages.success(self.request, "Password reset email has been sent successfully. Please check your email.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to send password reset email. Please try again.")
        return super().form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password-reset-done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password-reset-confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, "Password has been successfully reset.You can login")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "The password reset link is invalid or expired. Please request a new one.")
        return super().form_invalid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password-reset-complete.html'


# def login_form(request):


def is_superuser(user):
    return user.is_superuser  # Restrict access to superusers


@user_passes_test(is_superuser)
def add_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()  # Saves user, assigns role, and sends email
            messages.success(request, "User created successfully! Login credentials have been emailed.")
            return redirect('add_user')
    else:
        form = UserCreateForm()

    return render(request, 'registration/add_user.html', {'form': form})


def website_page(request):
    form = AppointmentForm()
    return render(request, 'Home/website/index.html', {'form': form})




@login_required
def notifications_inbox_view(request):
    # Fetch all notifications (Ensure `related_name="notifications"` in User model)
    notifications = request.user.notifications.all().order_by('-created_at')

    # Fetch all appointments
    appointments = Appointment.objects.all().order_by('-created_at')

    # Count unread (pending) appointments
    unread_appointments = appointments.filter(reply_status="pending").count()  # Adjust status as needed

    successful_replies = []
    failed_replies = []

    # Categorize appointment replies
    for appointment in appointments:
        if appointment.reply_status == 'success':
            successful_replies.append({
                'phone': appointment.phone,
                'message': appointment.reply_message
            })
        else:
            failed_replies.append({
                'phone': appointment.phone,
                'reason': appointment.reply_failure_reason
            })

    return render(request, 'Manage/inbox.html', {
        'notifications': notifications,
        'appointments': appointments,
        'unread_appointments': unread_appointments,  # ✅ Added to context
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
