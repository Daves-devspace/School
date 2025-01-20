from datetime import date, datetime

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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from apps.Manage.forms import CustomSignupForm
from apps.accounts.models import FeePayment
from apps.management.models import Term, SubjectMark, Attendance
from apps.students.models import Student, GradeSection
from apps.students.views import get_current_term
from apps.teachers.models import Teacher, Department


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
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)  # Logs the user in using Django sessions

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Store tokens in HttpOnly cookies
            response = redirect('home')  # Redirect to the home page
            response.set_cookie(
                'access_token', access_token, httponly=True, secure=True, samesite='Strict'
            )
            response.set_cookie(
                'refresh_token', refresh_token, httponly=True, secure=True, samesite='Strict'
            )

            messages.success(request, 'You are logged in!')
            return response

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







@login_required
def director_dashboard(request):
    current_year = date.today().year
    term = get_current_term()
    term_year = term.start_date.year

    # Fetching the total revenue for the current year
    total_revenue = FeePayment.objects.filter(date__year=current_year).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Fetching the total count of active students, teachers, and departments
    total_students = Student.objects.filter(status="active").count()
    total_teachers = Teacher.objects.count()
    total_departments = Department.objects.count()

    # Fetch all classes
    classes = GradeSection.objects.all()

    # List to store top 3 students for each class
    top_students_data = []

    # Loop through each class to calculate the top students
    for class_obj in classes:
        # Fetch all students in this class
        students = Student.objects.filter(grade=class_obj)

        # Get total marks for each student in each term and exam type
        student_marks = []
        for student in students:
            total_marks = SubjectMark.objects.filter(student=student).aggregate(
                total_marks=Sum('marks')
            )['total_marks'] or 0  # Default to 0 if no marks found

            student_marks.append({
                'student': student,
                'total_marks': total_marks,
            })

        # Sort students by total marks in descending order and get top 3
        student_marks.sort(key=lambda x: x['total_marks'], reverse=True)
        top_3_students = student_marks[:3]  # Get the top 3 students

        # Prepare the data for top 3 students with their class, term, exam type, and year
        for student_data in top_3_students:
            student = student_data['student']
            total_marks = student_data['total_marks']

            # Fetch the term and exam type for each student (use the first subject mark's term and exam type)
            subject_mark = SubjectMark.objects.filter(student=student).first()
            if subject_mark:
                term = subject_mark.term
                exam_type = subject_mark.exam_type
                year = term_year
            else:
                term = exam_type = year = None

            top_students_data.append({
                'student_name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'total_marks': total_marks,
                'class': class_obj.grade,
                'term': term.name if term else "N/A",
                'exam_type': exam_type.name if exam_type else "N/A",
                'year': year if year else "N/A",
            })

    # Render the home page with the context, including the top students data
    return render(request, 'Home/Admin/index.html', {
        "total_revenue": total_revenue,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_departments": total_departments,
        'current_year': current_year,
        'top_students_data': top_students_data,  # Pass the top students data to the template
    })


@login_required
def teacher_dashboard(request):
    # Check if the user belongs to the "Teacher" group
    if not request.user.groups.filter(name="Teacher").exists():
        return redirect("logout")

    # Retrieve the corresponding Teacher instance for the logged-in user
    teacher = get_object_or_404(Teacher, user=request.user)

    # Fetch the GradeSections assigned to the Teacher
    assigned_grade_sections = GradeSection.objects.filter(class_teacher=teacher)

    # Fetch attendance data for today
    today = date.today()
    attendance_records = Attendance.objects.filter(
        teacher=request.user,  # Ensure it's filtered by the logged-in teacher
        date=today
    )

    # Render the teacher dashboard template with attendance data
    return render(request, 'Home/Teacher/teacher-dashboard.html', {
        'assigned_grade_sections': assigned_grade_sections,
        'attendance_records': attendance_records,
        'today':today
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





#def login_form(request):



def website_page(request):
    return render(request,'Home/website/index.html')

