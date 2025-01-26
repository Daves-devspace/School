import json
import logging
from datetime import date, timedelta, datetime

from asgiref.sync import async_to_sync
from django.db.models import F, Value, CharField, Case, When
from django.db.models.functions import Concat


import requests
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions.datetime import TruncMonth, ExtractYear
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import make_aware, now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, TemplateView
from django_daraja.mpesa.core import MpesaClient
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import FeePayment, Expense
from apps.management.forms import SubjectForm, BookForm, TimetableForm, LessonExchangeForm, ProfileForm, \
    HolidayPresentationForm, FeedbackForm, TermForm
from apps.management.models import Term,ReportCard, SubjectMark, ExamType, \
    Attendance, Timetable, LessonExchangeRequest, HolidayPresentation
from apps.management.serializers import TimetableSerializer
from apps.schedules.models import Subject
from apps.students.forms import SendSMSForm, SendClassForm, ResultsSMSForm
from apps.students.models import Book, Transaction, Student, Payment, Parent, StudentParent, Grade, GradeSection

# Create your views here.
from django.db.models import Avg, Sum, Count, Q, Window

from apps.students.utils import MobileSasaAPI
from apps.students.views import get_current_term
from apps.teachers.models import Department, Teacher  # Revenue

logger = logging.getLogger(__name__)

def add_term(request):
    if request.method == 'POST':
        form = TermForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('terms')
    else:
        form = TermForm()
    return render(request,'Manage/terms.html',{'form': form})


def term_list(request):
    terms = Term.objects.all()
    return render(request,'Manage/term_list.html',{'terms': terms})


def edit_term(request,pk):
    term = get_object_or_404(Term,pk=pk)

    if request.method == 'POST':
        form = TermForm(request.POST,instance=term)
        if form.is_valid():
            form.save()
            return redirect('terms')
    else:
        form = TermForm(instance=term)

    return render(request,'Manage/edit_term.html',{'form':form,'term':term})


def send_notification(user, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": {"message": message},
        }
    )

@login_required
def user_profile(request):
    profile = request.user.profile  # Get the logged-in user's profile

    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)  # Handling file uploads
        if profile_form.is_valid():
            profile_form.save()
            return redirect('user_profile')  # Redirect after saving profile
    else:
        profile_form = ProfileForm(instance=profile)

    # Condition to check the role and render different sections
    if profile.is_teacher():
        # Add extra context or logic specific to teachers if needed
        additional_info = {
            "cv": profile.cv,
            "skills": profile.skills,
            "certifications": profile.certifications,
        }
    else:
        additional_info = {}

    return render(request, 'Manage/profile.html', {'profile_form': profile_form, 'profile': profile, 'additional_info': additional_info})

def create_presentation(request):
    if request.method == 'POST':
        form = HolidayPresentationForm(request.POST, request.FILES)
        if form.is_valid():
            presentation = form.save(commit=False)
            presentation.user_profile = request.user.profile  # Assign the current user's profile
            presentation.save()
            messages.success(request, "Presentation created successfully!")
            return redirect('presentations_list')  # Redirect to a list view of presentations
    else:
        form = HolidayPresentationForm()
    return render(request, 'Manage/create_presentation.html', {'form': form})


def presentation_detail(request,id):
    # Get the specific presentation
    presentation = get_object_or_404(HolidayPresentation, id=id)
    feedback_form = FeedbackForm(request.POST or None)

    if request.method == "POST" and feedback_form.is_valid():
        # Save feedback for the current presentation
        feedback = feedback_form.save(commit=False)
        feedback.presentation = presentation
        feedback.user = request.user  # Attach the current user to the feedback
        feedback.save()
        return redirect('presentation_detail', id=presentation.id)

    return render(request, 'Manage/presentation_detail.html', {
        'presentation': presentation,
        'feedback_form': feedback_form,
    })



@login_required
def submit_feedback(request, presentation_id):
    presentation = get_object_or_404(HolidayPresentation, id=presentation_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.presentation = presentation
            feedback.user = request.user
            feedback.save()
            messages.success(request, "Feedback submitted successfully!")
            return redirect('presentation_detail', presentation_id=presentation_id)
    else:
        form = FeedbackForm()
    return render(request, 'Manage/submit_feedback.html', {'form': form, 'presentation': presentation})


def presentation_list(request):
    presentations = HolidayPresentation.objects.all()
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # Handle feedback submission logic (save feedback, notify, etc.)
            form.save()
            return redirect('presentation_list')  # Redirect after successful feedback submission
    else:
        form = FeedbackForm()  # Feedback form for each presentation

    return render(request, 'Manage/presentation_list.html', {
        'presentations': presentations,
        'form': form
    })

@staff_member_required
def manage_users(request):
    users = User.objects.all()
    return render(request,'Manage/manage_users.html',{'users': users})

@staff_member_required
def toggle_user_status(request,user_id):
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = not user.is_active #toggle activation status
        user.save()
        status = "Activated" if user.is_active else "Deactivated"
        messages.success(request,f"User {user.username} has been {status}")
    except User.DoesNotExist:
        messages.error(request,"User not found")
    return redirect('manage_users')


def send_results_sms(request):
    if request.method == "POST":
        term_id = request.POST.get('term')
        exam_type_id = request.POST.get('exam_type')
        message_template = request.POST.get('message')

        try:
            # Validate selected Term and ExamType
            term = Term.objects.get(id=term_id)
            exam_type = ExamType.objects.get(id=exam_type_id)

            # Fetch active students
            active_students = Student.objects.filter(status="Active")

            personalized_messages = []
            for student in active_students:
                try:
                    # Fetch the report card for the student
                    report_card = ReportCard.objects.get(student=student, term=term, exam_type=exam_type)
                except ReportCard.DoesNotExist:
                    continue

                # Fetch the student's parent
                student_parent = StudentParent.objects.filter(student=student).first()
                if not student_parent or not student_parent.parent.mobile:
                    continue

                try:
                    message = message_template.format(
                        parent_name=student_parent.parent.first_name,
                        student_name=student.first_name,
                        student_class=student.grade,
                        total_marks=report_card.total_marks(),
                        rank=report_card.student_rank(),
                        subject_results=", ".join(
                            [f"{subj.subject.name}: {subj.marks}" for subj in report_card.subject_marks.all()]
                        ),
                        term=term.name,
                        exam_type=exam_type.name
                    )
                except KeyError as e:
                    messages.error(request, f"Message template key error: {e}. Check your template.")
                    return redirect('result_sms')

                personalized_messages.append({
                    "phone": student_parent.parent.mobile,
                    "message": message
                })

            # Use MobileSasaAPI to send the SMS
            if personalized_messages:
                mobile_api = MobileSasaAPI()
                api_responses = mobile_api.send_bulk_personalized_sms(personalized_messages)

                # Check the first response in the list
                if api_responses and isinstance(api_responses, list) and api_responses[0]['status']:
                    messages.success(
                        request,
                        f"SMS sent successfully to {len(personalized_messages)} recipients."
                    )
                else:
                    error_message = api_responses[0]['message'] if api_responses else "Unknown error"
                    messages.error(request, f"Failed to send SMS: {error_message}")
            else:
                messages.warning(request, "No valid parents with mobile numbers found to send SMS.")

            return redirect('result_sms')

        except (Term.DoesNotExist, ExamType.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}. Please ensure the Term and Exam Type exist.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {str(e)}.")

        return redirect('result_sms')

    # Render the form for GET request
    terms = Term.objects.all()
    exam_types = ExamType.objects.all()
    return render(request, 'Manage/send_result_sms.html', {'terms': terms, 'exam_types': exam_types})






@login_required
def send_bulk_sms_view(request):
    parents = Parent.objects.filter(mobile__isnull=False)
    phone_numbers = [str(parent.mobile) for parent in parents]

    if request.method == "POST":
        form = SendSMSForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]

            # Use MobileSasaAPI to send the SMS
            api = MobileSasaAPI()
            response = api.send_bulk_sms(message, phone_numbers)

            # Check response and set messages
            if response and all(res.get("status") for res in response):
                messages.success(request, "SMS sent successfully to all parents!")
            else:
                messages.error(request, "Failed to send SMS to some or all parents.")

            return redirect("send_bulk_sms")  # Redirect to avoid re-submission
    else:
        # If it's a GET request, display the form
        form = SendSMSForm()

    return render(request, "manage/send_sms.html", {"form": form})


def send_sms_to_class(request):
    success = None  # Variable to track the success status
    message = None  # Variable to track the success message
    error = None  # Variable to track the error message

    if request.method == 'POST':
        form = SendClassForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            class_choice = form.cleaned_data['class_choice']

            # Filter StudentParent objects based on the selected class
            student_parents = StudentParent.objects.filter(student__grade=class_choice)

            # Extract the phone numbers of the parents
            phone_numbers = [str(student_parent.parent.mobile) for student_parent in student_parents if
                             student_parent.parent.mobile]

            # Check if there are phone numbers to send SMS to
            if not phone_numbers:
                error = "No phone numbers found for the selected class."
            else:
                # Send SMS using MobileSasaAPI
                api = MobileSasaAPI()
                response = api.send_bulk_sms(message, phone_numbers)  # Assuming this is how the API works

                # Check if the SMS was sent successfully
                if response and response[0].get("status") == "success":
                    success = True
                    message = f"SMS successfully sent to {len(phone_numbers)} parents in {class_choice.name}."
                else:
                    error = "Failed to send SMS. Please try again later."
        else:
            error = "Invalid form data. Please ensure all fields are filled correctly."

    else:
        form = SendClassForm()

    return render(request, "Manage/filter_and_send_sms.html", {
        "form": form,
        "success": success,
        "message": message,
        "error": error
    })

#
# def messages_view(request):
#     grades = Class.objects.all()  # Fetch grades for the dropdown
#
#     if request.method == "POST":
#         form = BulkSMSForm(request.POST)
#
#         if form.is_valid():
#             selected_parents = form.cleaned_data["parents"]
#             message = form.cleaned_data["message"]
#
#             if not selected_parents:
#                 messages.error(request, "No parents were selected.")
#                 return redirect("messages")
#
#             # Proceed with SMS sending
#             api = MobileSasaAPI()
#             failed_sends = []
#
#             for parent_id in selected_parents:
#                 parent = get_object_or_404(StudentParent, pk=parent_id).parent
#                 response = api.send_single_sms(str(parent.mobile), message)
#
#                 if not response or not response.get("status"):
#                     failed_sends.append(parent)
#
#             if not failed_sends:
#                 messages.success(request, "SMS sent successfully to all selected parents!")
#             else:
#                 messages.warning(
#                     request,
#                     f"Failed to send SMS to {len(failed_sends)} parent(s): "
#                     f"{', '.join([str(parent) for parent in failed_sends])}"
#                 )
#             return redirect("messages")
#
#     else:
#         form = BulkSMSForm()
#
#     return render(request, "Manage/bulk_sms.html", {"form": form, "grades": grades})


def messages_view(request):
    grades = Grade.objects.all()  # Fetch all grades for the dropdown

    # Default form data
    selected_grade = None
    parents_choices = []

    if request.method == "POST":
        form = BulkSMSForm(request.POST)

        # Handle form submission for SMS
        if "message" in request.POST and form.is_valid():
            selected_parents = form.cleaned_data["parents"]
            message = form.cleaned_data["message"]

            if not selected_parents:
                messages.error(request, "No parents were selected.")
                return redirect("messages")

            # Send SMS to selected parents
            api = MobileSasaAPI()
            failed_sends = []

            for parent_id in selected_parents:
                parent = get_object_or_404(StudentParent, pk=parent_id).parent
                response = api.send_single_sms(str(parent.mobile), message)

                if not response or not response.get("status"):
                    failed_sends.append(parent)

            if not failed_sends:
                messages.success(request, "SMS sent successfully to all selected parents!")
            else:
                messages.warning(
                    request,
                    f"Failed to send SMS to {len(failed_sends)} parent(s): "
                    f"{', '.join([str(parent) for parent in failed_sends])}"
                )
            return redirect("messages")

        # Handle grade selection for filtering
        elif "grade" in request.POST:
            selected_grade = request.POST.get("grade")
            parents = StudentParent.objects.filter(student__grade_id=selected_grade) if selected_grade else StudentParent.objects.all()
            parents_choices = [
                (p.id, f"{p.parent.first_name} {p.parent.last_name} ({p.student.first_name})")
                for p in parents
            ]
    else:
        # Initialize form for GET request
        form = BulkSMSForm()

    # Populate grade and parents choices dynamically
    form.fields["grade"].choices = [("", "All Grades")] + [(g.id, g.name) for g in grades]
    form.fields["parents"].choices = parents_choices

    return render(request, "Manage/bulk_sms.html", {
        "form": form,
        "selected_grade": selected_grade,
        "parents_choices": parents_choices
    })



# @csrf_exempt
# def send_sms(request):
#     if request.method == "POST":
#         phone = request.POST.get("phone")
#         message = request.POST.get("message")
#
#         if not phone or not message:
#             return JsonResponse({
#                 "status": "error",
#                 "message": "Phone number and message are required."
#             })
#
#         api = MobileSasaAPI()  # Initialize the MobileSasaAPI class
#
#         try:
#             response = api.send_single_sms(message=message, phone=phone)  # Use the utility method
#
#             if response.get("status"):  # Check if the API returned success
#                 return JsonResponse({
#                     "status": "success",
#                     "message": "SMS sent successfully",
#                     "messageId": response.get("messageId")
#                 })
#             else:
#                 return JsonResponse({
#                     "status": "error",
#                     "message": response.get("message", "Unknown error occurred.")
#                 })
#
#         except Exception as e:
#             return JsonResponse({
#                 "status": "error",
#                 "message": f"An error occurred: {str(e)}"
#             })
#
#     return JsonResponse({
#         "status": "error",
#         "message": "Invalid request method."
#     })


def send_sms_view(request, student_parent_id):
    # Fetch the specific StudentParent instance
    student_parent = get_object_or_404(StudentParent, id=student_parent_id)

    # Get the related parent's phone number
    parent = student_parent.parent

    if request.method == "POST":
        form = SendReminderForm(request.POST)
        if form.is_valid():
            # Phone is pre-filled, fetch directly from the parent
            phone = str(parent.mobile)
            message = form.cleaned_data["message"]

            # Use MobileSasaAPI to send the SMS
            api = MobileSasaAPI()
            response = api.send_single_sms(phone, message)

            # Respond with success or failure
            if response and response.get("status"):
                messages.success(request, "SMS sent successfully!")
            else:
                messages.warning(request, "Failed to send SMS. {response.get('message', 'Unknown error')}")
            return redirect("success-page")  # Replace with your actual success page
    else:
        # Pre-fill the phone field
        form = SendSMSForm(initial={"phone": str(parent.mobile)})

    return render(request, "manage/send_sms.html", {"form": form, "student_parent": student_parent})


@login_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject_name = form.cleaned_data[
                'name'].strip()  # Don't normalize the name here if you want to preserve original case
            grades_selected = form.cleaned_data['grade']  # Get the grades selected in the form
            single_grade_selected = form.cleaned_data['single_grade']  # Get the single grade, if any

            # Check if the subject already exists (case insensitive)
            existing_subject = Subject.objects.filter(name__iexact=subject_name).first()

            if existing_subject:
                # If the subject exists, check for new grades to add
                existing_grades = existing_subject.grade.all()
                new_grades = grades_selected.exclude(id__in=existing_grades.values_list('id', flat=True))

                if new_grades.exists():
                    # Add the new grades to the existing subject
                    existing_subject.grade.add(*new_grades)
                    messages.success(
                        request,
                        f"Updated '{existing_subject.name}' to include new grades: {', '.join(grade.name for grade in new_grades)}."
                    )
                else:
                    messages.info(
                        request,
                        f"No new grades were added. '{existing_subject.name}' already has the selected grades."
                    )

                # Check and set the single_grade if provided
                if single_grade_selected:
                    existing_subject.single_grade = single_grade_selected
                    existing_subject.save()
                    messages.success(
                        request,
                        f"Updated the 'single grade' for '{existing_subject.name}' to {single_grade_selected.name}."
                    )

                return redirect('subjects_list')

            else:
                # Create a new subject if it doesn't exist
                new_subject = form.save()

                # If a single grade is provided, assign it to the new subject
                if single_grade_selected:
                    new_subject.single_grade = single_grade_selected
                    new_subject.save()
                    messages.success(
                        request,
                        f"Subject '{new_subject.name}' added successfully with the single grade {single_grade_selected.name}."
                    )
                else:
                    messages.success(request, f"Subject '{new_subject.name}' added successfully!")

                return redirect('subjects_list')

    else:
        form = SubjectForm()

    return render(request, 'performance/add_subject.html', {'form': form})


def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('books_in_store')  # redirect to books in store/available
    else:
        form = BookForm()

    return render(request, 'library/add_book.html', {'form': form})


@login_required
def dashboard(request):
    # Count the number of students
    student_count = Student.objects.count()

    # Count the number of teachers
    teacher_count = Teacher.objects.count()

    # Count the number of departments
    department_count = Department.objects.count()

    # # Calculate the total revenue (assuming Revenue is a model with a 'amount' field)
    # total_revenue = Revenue.objects.aggregate(total_revenue=models.Sum('amount'))['total_revenue'] or 0
    print(f"Student Count: {student_count}")

    return render(request, "Home/Admin/index.html", {
        "student_count": student_count,
        "teacher_count": teacher_count,
        "department_count": department_count,
        # "total_revenue": total_revenue
    })


# get student to feth marks
@login_required
def get_student(request):
    queryset = Student.objects.all()
    ranks = Student.objects.annotate(marks=Sum('studentmarks__marks')).order_by('-marks', 'grade')
    for rank in ranks:
        print(rank.marks)
    if request.GET.get('search'):
        search = request.GET.get('search')
        queryset = queryset.filter(
            Q(student_name__icontains=search) |
            Q(department__department__icontains=search) |
            Q(student_id__student_id__contains=search) |
            Q(student_email__icontains=search) |
            Q(student_age__icontains=search)
        )

    return render(request, 'students/students.html', {'queryset': queryset})


@login_required
def generate_report_card():
    current_rank = -1
    ranks = Student.objects.annotate(
        marks=Sum('studentmarks__marks')).order_by('-marks')
    i = 1

    for rank in ranks:
        ReportCard.objects.create(
            student=rank,
            student_rank=i
        )
        i = i + 1


# # teachers adding results
# @login_required
# def add_results(request):
#     if request.method == 'POST':
#         form = AddResultForm(request.POST)
#         if form.is_valid():
#             student = form.cleaned_data['student']
#             teacher_subject = form.cleaned_data['teacher_subject']
#             term = form.cleaned_data['term']
#             score = form.cleaned_data['score']
#
#             # Check if result already exists
#             existing_result = Result.objects.filter(
#                 student=student,
#                 teacher_subject=teacher_subject,
#                 term=term
#             ).exists()
#
#             if existing_result:
#                 messages.error(request, "Result already exists for this student, subject, and term.")
#             else:
#                 Result.objects.create(
#                     student=student,
#                     teacher_subject=teacher_subject,
#                     term=term,
#                     score=score
#                 )
#                 messages.success(request, "Result added successfully!")
#             return redirect('add_results')
#     else:
#         form = AddResultForm()
#
#     return render(request, 'performance/add_results.html', {'form': form})


def get_students_by_class(request):
    class_id = request.GET.get('class_id')
    if class_id:
        students = Student.objects.filter(class_name_id=class_id).values('id', 'first_name', 'last_name')
        return JsonResponse(list(students), safe=False)
    return JsonResponse([], safe=False)


@login_required
def view_results(request):
    results = Result.objects.select_related('student', 'teacher_subject__teacher', 'teacher_subject__subject', 'term')
    return render(request, 'performance/results.html', {'results': results})


@login_required
def list_subjects(request):
    subjects = Subject.objects.all()  # or use any other filter you need
    return render(request, 'performance/subjects.html', {'subjects': subjects})


# Edit Subject
def edit_subject(request, id):
    subject = get_object_or_404(Subject, pk=id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subjects_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'performance/edit_subject.html', {'form': form})


@login_required
def subject_teachers(request):
    teacher_subjects = Subject.objects.select_related('teacher', 'subject',
                                                             'grade_assigned').all()  # or use any other filter you need
    return render(request, 'performance/subject_teachers.html', {'teacher_subjects': teacher_subjects})


@login_required
def subjects_by_grade(request, grade_id):
    grade = Grade.objects.get(id=grade_id)
    subjects = Subject.objects.filter(grade_assigned=grade).select_related('teacher', 'subject',
                                                                                  'grade_assigned')
    return render(request, 'performance/subjects.html', {'grade': grade, 'subjects': subjects})


# top 5 students
@login_required
def class_performance(request):
    results = Result.objects.filter().values(
        'student__first_name'
    ).annotate(total_score=Sum('score')).order_by('-total_score')

    top_students = results[:5]
    return render(request, 'performance/class_performance.html', {
        'top_students': top_students,
        'results': results,
    })


# Filter Results View
def filter_results(request):
    # Fetch filter parameters
    grade_id = request.GET.get('grade_id')
    term_id = request.GET.get('term_id')
    subject_id = request.GET.get('subject_id')
    exam_type_id = request.GET.get('exam_type_id')

    # Redirect to the results table if all parameters are provided
    if grade_id and term_id and subject_id and exam_type_id:
        return redirect(
            reverse('add_results_table') +
            f'?grade_id={grade_id}&term_id={term_id}&subject_id={subject_id}&exam_type_id={exam_type_id}'
        )

    # Populate filter form options
    grades = GradeSection.objects.all()
    terms = Term.objects.annotate(
        display_name=Concat(
            F('name'),
            Value(' - '),
            F('start_date__year'),
            output_field=CharField()
        )
    )
    subjects = Subject.objects.all()
    exam_types = ExamType.objects.all()

    return render(request, 'performance/filter_form.html', {
        'classes': grades,
        'terms': terms,
        'subjects': subjects,
        'exam_types': exam_types,
    })


# Add or Update Results Table View


def add_results_table(request):
    # Get query parameters
    class_id = request.GET.get('grade_id')
    term_id = request.GET.get('term_id')
    subject_id = request.GET.get('subject_id')
    exam_type_id = request.GET.get('exam_type_id')

    # Redirect to filter_results if any parameter is missing
    if not (class_id and term_id and subject_id and exam_type_id):
        return redirect('filter_results')

    # Fetch the objects based on the provided IDs
    selected_grade_section = get_object_or_404(GradeSection, id=class_id)
    selected_term = get_object_or_404(Term, id=term_id)
    selected_subject = get_object_or_404(Subject, id=subject_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    # Fetch students in the selected grade section
    students = Student.objects.filter(grade=selected_grade_section)

    # Prepare initial data for students' marks
    initial_data = []
    subject_marks_dict = {
        sm.student.id: sm for sm in SubjectMark.objects.filter(
            student__in=students,
            subject=selected_subject,
            term=selected_term,
            exam_type=selected_exam_type
        )
    }

    for student in students:
        subject_mark = subject_marks_dict.get(student.id)
        marks = subject_mark.marks if subject_mark else None
        initial_data.append({
            'student': student,
            'marks': marks
        })

    # Handling form submission (POST)
    if request.method == 'POST':
        max_score = float(request.POST.get('max_score', 100))  # Default max score if not provided

        for student in students:
            marks = request.POST.get(f'marks_{student.id}')
            if marks:
                try:
                    marks = float(marks)
                    # Ensure marks are within range
                    if 0 <= marks <= max_score:
                        subject_mark, created = SubjectMark.objects.update_or_create(
                            student=student,
                            subject=selected_subject,
                            term=selected_term,
                            exam_type=selected_exam_type,
                            defaults={'marks': marks, 'max_score': max_score}
                        )
                    else:
                        raise ValueError(f"Marks should be between 0 and {max_score}")
                except ValueError as e:
                    messages.error(request, f"Invalid marks for {student.first_name} {student.last_name}: {e}")
                    continue
        messages.success(request, "Marks have been successfully updated!")
        return redirect('view_results_table', grade_id=class_id, term_id=term_id, subject_id=subject_id,
                        exam_type_id=exam_type_id)

    context = {
        'selected_grade_section': selected_grade_section,
        'selected_term': selected_term,
        'selected_subject': selected_subject,
        'selected_exam_type': selected_exam_type,
        'students': students,
        'initial_data': initial_data
    }

    return render(request, 'performance/add_results_table.html', context)


def view_results_table(request, grade_id, term_id, exam_type_id, subject_id):
    # Get the GradeSection based on grade_id
    selected_grade_section = get_object_or_404(GradeSection, id=grade_id)

    # Fetch the associated Grade from the GradeSection
    selected_class = selected_grade_section.grade

    # Get selected term, exam type, and subject
    selected_term = get_object_or_404(Term, id=term_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    # Fetch all subjects that the students are taking
    subjects = Subject.objects.all()  # You can modify this to filter subjects by grade if needed

    # Fetch all GradeSections for the selected grade (e.g., all sections for Grade1)
    grade_sections = GradeSection.objects.filter(grade=selected_class)

    # Fetch all students from the selected grade's sections
    students = Student.objects.filter(grade__in=grade_sections)

    student_data = []
    for student in students:
        marks = []
        total_marks = 0

        # Get marks for each subject the student is taking
        for subject in subjects:
            subject_mark = SubjectMark.objects.filter(
                student=student,
                subject=subject,
                term=selected_term,
                exam_type=selected_exam_type
            ).first()

            # If marks are available, calculate percentage and add to the list
            if subject_mark and subject_mark.marks != "-":
                # Calculate the percentage if marks are available
                percentage = round((subject_mark.marks / subject_mark.max_score) * 100)
                marks.append(f"{percentage}%")  # Append percentage with % symbol
                total_marks += percentage  # Add percentage to total_marks for rank calculation
            else:
                marks.append("-")

        student_data.append({
            'admission_number': student.admission_number,
            'name': f"{student.first_name} {student.last_name}",
            'marks': marks,
            'total_marks': total_marks,
        })

    # Sort by total_marks in descending order
    student_data = sorted(student_data, key=lambda x: x['total_marks'], reverse=True)

    # Add ranking
    for index, student in enumerate(student_data):
        student['rank'] = index + 1

    context = {
        'selected_class': selected_class,
        'selected_term': selected_term,
        'selected_exam_type': selected_exam_type,
        'subjects': subjects,
        'grade_sections': grade_sections,
        'student_data': student_data,
    }

    return render(request, 'performance/view_results_table.html', context)



def report_card_view(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)

    # Fetch or create the report card for the student and term
    report_card, created = ReportCard.objects.get_or_create(student=student, term=term)

    # Calculate total marks and rank
    total_marks = report_card.total_marks()  # Assuming `total_marks` method is defined in your ReportCard model
    rank = report_card.student_rank()  # Assuming `student_rank` method is defined in your ReportCard model

    # Fetch subject marks for the student in the given term
    subject_marks = SubjectMark.objects.filter(student=student, term=term)

    # Prepare subject-wise marks for display
    subject_marks_data = []
    for subject_mark in subject_marks:
        subject_marks_data.append({
            'subject': subject_mark.subject.name,
            'marks': subject_mark.marks,
        })

    # Return the data as JSON to be used dynamically
    return JsonResponse({
        'total_marks': total_marks,
        'rank': rank,
        'subject_marks': subject_marks_data,  # Include subject-wise marks
    })


def view_report_card(request, student_id, term_id, exam_type_id):
    # Fetch the student, term, and exam type
    student = get_object_or_404(Student, id=student_id)
    selected_term = get_object_or_404(Term, id=term_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    # Fetch the marks for the selected student, term, and exam type
    subjects = Subject.objects.filter(grade=student.grade)
    subject_marks = {}
    total_marks = 0

    for subject in subjects:
        subject_mark = SubjectMark.objects.filter(
            student=student,
            subject=subject,
            term=selected_term,
            exam_type=selected_exam_type
        ).first()

        if subject_mark:
            subject_marks[subject.name] = subject_mark.marks
            total_marks += subject_mark.marks
        else:
            subject_marks[subject.name] = "-"

    # Calculate average marks
    average_marks = total_marks / len(subjects) if subjects else 0

    context = {
        'student': student,
        'selected_term': selected_term,
        'selected_exam_type': selected_exam_type,
        'subject_marks': subject_marks,
        'total_marks': total_marks,
        'average_marks': average_marks,
    }

    return render(request, 'performance/view_report_card.html', context)


def top_students_view(request):
    term = get_current_term()
    term_year = term.start_date.year

    # Fetch all classes
    classes = Grade.objects.all()

    # List to store top 3 students for each class
    top_students_data = []

    # Loop through each class to calculate the top students
    for class_obj in classes:
        # Fetch all students in this class
        students = Student.objects.filter(grade__grade=class_obj)

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

        # Sort students by total marks in descending order
        student_marks.sort(key=lambda x: x['total_marks'], reverse=True)

        # Initialize rank to 1 for this class
        rank = 1

        # Get top 3 students
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
                year = term_year  # Assuming the term has a year field
            else:
                term = exam_type = year = None

            # Access grade and section information
            grade_section = student.grade  # This gives the GradeSection object
            grade_section_display = f"{grade_section.grade.name} {grade_section.section.name}" if grade_section else "N/A"

            top_students_data.append({
                'student_name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'total_marks': total_marks,
                'grade_section': grade_section_display,
                'term': term.name if term else "N/A",
                'exam_type': exam_type.name if exam_type else "N/A",
                'year': year if year else "N/A",
                'rank': rank,
            })

            # Increment rank for the next student
            rank += 1

    # Context to pass to the template
    context = {
        'top_students_data': top_students_data,
    }

    return render(request, 'performance/top_students.html', context)





# calculating performance by grade and term
@login_required
def grade_performance_view(request, grade_id, term_id):
    grade = Class.objects.get(id=grade_id)
    term = Term.objects.get(id=term_id)
    performances = Performance.objects.filter(
        student__grade=grade,
        term=term
    ).select_related("student", "subject")

    # Aggregate data
    student_performance = (
        performances.values("student__first_name", "student__last_name")
        .annotate(
            average_percentage=Avg("marks") / Avg("total_marks") * 100,
            total_marks=Avg("total_marks"),
            total_obtained_marks=Avg("marks"),
        )
    )

    context = {
        "grade": grade,
        "term": term,
        "student_performance": student_performance,
    }
    return render(request, "performance/student_performance.html", context)


@login_required
def books_in_store(request):
    books = Book.objects.all()
    return render(request, 'library/books_in_store.html', {'books': books})


@login_required
def borrowed_books(request):
    borrowed = Transaction.objects.filter(status='BORROWED')
    return render(request, 'library/borrowed_books.html', {"borrowed_items": borrowed})


@login_required
def book_fines(request):
    transactions = Transaction.objects.all()
    fines = [t for t in transactions if t.total_fine > 0]
    return render(request, 'library/book_fines.html', {'fines': fines})


@login_required
def issue_book(request, id):
    book = get_object_or_404(Book, pk=id)
    students = Student.objects.all()
    if request.method == 'POST':
        student_id = request.POST['student_id']
        student = Student.objects.get(pk=student_id)
        expected_return_date = date.today() + timedelta(days=7)
        transaction = Transaction.objects.create(book=book, student=student, expected_return_date=expected_return_date,
                                                 status='BORROWED')
        transaction.save()
        messages.success(request, f'Book {book.title} was borrowed successfully')
        return redirect('books_in_store')

    return render(request, 'library/issue.html', {'book': book, 'students': students})


@login_required
def return_book(request, id):
    transaction = get_object_or_404(Transaction, pk=id)
    transaction.return_date = date.today()
    transaction.status = 'RETURNED'
    transaction.save()
    messages.success(request, f'Book {transaction.book.title} was returned successfully')
    if transaction.total_fine > 0:
        messages.warning(request, f'Book {transaction.book.title} has incurred a fine of Ksh.{transaction.total_fine}')
    return redirect('books_in_store')


@login_required
def line_chart(request):
    # Get all FeePayments for the current year
    current_year = date.today().year
    fee_payments = FeePayment.objects.filter(date__year=2024)

    fee_payments = FeePayment.objects.filter(date__year=current_year).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total_revenue=Sum('amount')).order_by('month')

    # Prepare the data for the chart

    months = []
    totals = []
    for payment in fee_payments:
        totals.append(payment['total_revenue'] or 0)  # Use 0 if no revenue for the month
        months.append(payment['month'].strftime("%b"))  # Format the month as "Jan", "Feb", etc.

    total_revenue = sum(totals)  # total revenue of the year

    return JsonResponse({
        "title": f"Revenue Grouped By Month",
        "data": {
            "labels": months,
            "datasets": [{
                "label": "Revenue",
                "lineTension": 0.01,
                "backgroundColor": "linear-gradient(90deg, #0a3622 0%, #008374 100%)",
                "borderColor": "rgba(78, 115, 223, 1)",
                "pointRadius": 3,
                "pointBackgroundColor": "rgba(78, 115, 223, 1)",
                "pointBorderColor": "rgba(78, 115, 223, 1)",
                "pointHoverRadius": 3,
                "pointHoverBackgroundColor": "rgba(78, 115, 223, 1)",
                "pointHoverBorderColor": "rgba(78, 115, 223, 1)",
                "pointHitRadius": 10,
                "pointBorderWidth": 2,
                "data": totals,
            }],
        },
        "total_revenue": total_revenue  # Include total revenue
    })


# revenue chart

@login_required
def dashboard_view(request):
    current_year = date.today().year
    total_revenue = FeePayment.objects.filter(date__year=current_year).aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(request, "Home/Admin/index.html", {"total_revenue": total_revenue})





@login_required
def pie_data(request):
    # Count boys and girls in your dataset
    boys_count = Student.objects.filter(gender='Male', status='Active').count()
    girls_count = Student.objects.filter(gender='Female', status='Active').count()

    return JsonResponse({
        "title": "Gender Ratio",
        "labels": ["Boys", "Girls"],  # Labels for the pie chart
        "datasets": [{
            "data": [boys_count, girls_count],  # Pie chart data
            "backgroundColor": ['#0a3622', '#20b370'],  # Colors for boys and girls
            "hoverBackgroundColor": ['#2e59d9', '#e57373'],  # Hover colors
            "hoverBorderColor": "rgba(234, 236, 244, 1)",
        }]
    })




@login_required
def trends_bar_chart_data(request):
    current_year = datetime.now().year

    # Fetch all students grouped by month and gender
    monthly_data = (
        Student.objects.filter(joining_date__year=current_year)
        .values('gender', 'joining_date__month')
        .annotate(count=Count('id'))  # Count the number of students
    )

    # Initialize monthly counts
    monthly_boys = [0] * 12
    monthly_girls = [0] * 12

    # Populate the monthly counts
    for entry in monthly_data:
        month = entry['joining_date__month'] - 1  # Month index (0-based)
        if entry['gender'] == "Male":
            monthly_boys[month] += entry['count']
        elif entry['gender'] == "Female":
            monthly_girls[month] += entry['count']

    # Return JSON response
    return JsonResponse({
        "title": "Yearly Enrollment Trends",
        "labels": [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ],
        "datasets": [
            {
                "label": "Boys",
                "backgroundColor": "rgba(78, 115, 223, 0.5)",  # Blue
                "borderColor": "rgba(78, 115, 223, 1)",
                "data": monthly_boys,
            },
            {
                "label": "Girls",
                "backgroundColor": "rgba(28, 200, 138, 0.5)",  # Green
                "borderColor": "rgba(28, 200, 138, 1)",
                "data": monthly_girls,
            }
        ]
    })



@login_required
def bar_chart(request):
    transactions = Transaction.objects.filter(created_at__year=2024)
    grouped = transactions.annotate(month=TruncMonth('created_at')).values('month').annotate(
        count=Count('id')).order_by('month')
    numbers = []
    months = []
    for i in grouped:
        numbers.append(i['count'])
        months.append(i['month'].strftime('%b'))
    print(months)
    return JsonResponse({
        "title": "Transactions Grouped By Month",
        "data": {
            "labels": months,
            "datasets": [{
                "label": "Total",
                "backgroundColor": "#4e73df",
                "hoverBackgroundColor": "#2e59d9",
                "borderColor": "#4e73df",
                "data": numbers,
            }],
        },
    })


@login_required
def lost_book(request, id):
    transactions = Transaction.objects.get(id=id)
    transactions.status = 'LOST'
    transactions.return_date = date.today()
    transactions.save()
    messages.error(request, 'Book registered as lost!')
    return redirect('borrowed_books')


@login_required
def pay_overdue(request, id):
    transaction = Transaction.objects.get(pk=id)
    total = transaction.total_fine
    phone = transaction.student.parent_mobile
    cl = MpesaClient()
    phone_number = '0115429140'
    amount = 1
    account_reference = 'transaction.student.admission_number'
    transaction_desc = 'Fines'
    callback_url = 'ngroks.app/handle/payment/transactions'
    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
    if response.response_code == "0":
        payment = Payment.objects.create(transaction=transaction, merchant_request_id=response.merchant_request_id,
                                         checkout_request_id=response.checkout_request_id, amount=amount)
        payment.save()
        messages.success(request, f'Your payment was triggered successfully')
    return redirect('book_fines')


@login_required
@csrf_exempt
def callback(request):
    resp = json.loads(request.body)
    data = resp['Body']['stkcallback']
    if data["ResultCode"] == "0":
        m_id = data["MerchantRequestID"]
        c_id = data["CheckoutRequestID"]
        code = ""
        item = data["CallbackMetadata"]["Item"]
        for i in item:
            name = i["Name"]
            if name == "MpesaRecieptNumber":  # if name=name......in response body
                code = i["Value"]
        transaction = Transaction.objects.get(merchant_request_id=m_id, checkout_request_id=c_id)
        transaction.code = code
        transaction.status = "COMPLETED"
        transaction.save()
    return HttpResponse("ok")


@login_required
def data_trends(request):
    return render(request, 'Home/trends.html')


@login_required
def revenue_line_chart(request):
    current_year = date.today().year

    # Get all FeePayments for the current year grouped by month
    fee_payments = FeePayment.objects.filter(date__year=current_year).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total_revenue=Sum('amount')).order_by('month')

    # Get all Expenses for the current year grouped by month
    expenses = Expense.objects.filter(date__year=current_year).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(total_expenses=Sum('amount')).order_by('month')

    # Extract unique months from both datasets
    all_months = sorted(
        set(payment['month'] for payment in fee_payments)
        | set(expense['month'] for expense in expenses)
    )

    # Prepare data for the chart
    months = []
    revenue_totals = []
    expense_totals = []

    # Create dictionaries for quick lookup of revenues and expenses
    revenue_dict = {payment['month']: payment['total_revenue'] or 0 for payment in fee_payments}
    expense_dict = {expense['month']: expense['total_expenses'] or 0 for expense in expenses}

    for month in all_months:
        months.append(month.strftime("%b"))  # Format month as "Jan", "Feb", etc.
        revenue_totals.append(revenue_dict.get(month, 0))  # Default to 0 if no data
        expense_totals.append(expense_dict.get(month, 0))  # Default to 0 if no data

    # Prepare the JSON response data
    chart_data = {
        "title": f"Revenue and Expenses Grouped By Month for {current_year}",
        "data": {
            "labels": months,
            "datasets": [
                {
                    "label": "Revenue",
                    "lineTension": 0.2,
                    "backgroundColor": "rgba(173, 216, 230, 0.2)",  # Light blue fill (RGBA with opacity)
                    "borderColor": "rgba(173, 216, 230, 1)",  # Light blue line
                    "pointRadius": 3,
                    "pointBackgroundColor": "rgba(173, 216, 230, 1)",
                    "pointBorderColor": "rgba(173, 216, 230, 1)",
                    "pointHoverRadius": 3,
                    "pointHoverBackgroundColor": "rgba(173, 216, 230, 1)",
                    "pointHoverBorderColor": "rgba(173, 216, 230, 1)",
                    "pointHitRadius": 10,
                    "pointBorderWidth": 2,
                    "data": revenue_totals,
                    "fill": True,  # Fill the area beneath the line
                },
                {
                    "label": "Expenses",
                    "lineTension": 0.1,
                    "backgroundColor": "rgba(0, 131, 116, 0.2)",  # Accent green fill with opacity
                    "borderColor": "rgba(0, 131, 116, 1)",  # Accent green line
                    "pointRadius": 3,
                    "pointBackgroundColor": "rgba(0, 131, 116, 1)",
                    "pointBorderColor": "rgba(0, 131, 116, 1)",
                    "pointHoverRadius": 3,
                    "pointHoverBackgroundColor": "rgba(0, 131, 116, 1)",
                    "pointHoverBorderColor": "rgba(0, 131, 116, 1)",
                    "pointHitRadius": 10,
                    "pointBorderWidth": 2,
                    "data": expense_totals,
                    "fill": True,  # Fill the area beneath the line
                },
            ],
        },
        "total_revenue": sum(revenue_totals),
        "total_expenses": sum(expense_totals),
    }

    # Return the JSON response
    return JsonResponse(chart_data)


@login_required
def mark_attendance(request, grade_section_id, term_id):
    # Get the teacher's assigned GradeSection
    grade_section = get_object_or_404(GradeSection, id=grade_section_id, class_teacher=request.user)

    # Fetch the list of students in the GradeSection
    students = Student.objects.filter(grade=grade_section)

    # Fetch the term object
    term = get_object_or_404(Term, id=term_id)

    # If attendance is being submitted
    if request.method == 'POST':
        for student in students:
            # Get attendance status and reason for absence
            is_present = request.POST.get(f'present_{student.id}', 'off') == 'on'
            absence_reason = request.POST.get(f'absence_reason_{student.id}', '')

            # Update or create attendance record
            Attendance.objects.update_or_create(
                student=student,
                section=grade_section,
                teacher=request.user,
                date=now().date(),  # Ensure attendance is recorded for today
                term=term,
                defaults={'is_present': is_present, 'absence_reason': absence_reason}
            )

        # Redirect to confirmation or a summary page
        return redirect('attendance_summary', grade_section_id=grade_section.id, term_id=term.id)

    return render(request, 'Manage/mark_attendance.html', {
        'grade_section': grade_section,
        'students': students,
        'term': term,
    })



def attendance_summary(request, grade_section_id, term_id):
    # Get the GradeSection and Term
    grade_section = get_object_or_404(GradeSection, id=grade_section_id)
    term = get_object_or_404(Term, id=term_id)

    # Fetch attendance records grouped by student
    attendance_records = (
        Attendance.objects.filter(section=grade_section, term=term)
        .values('student__id', 'student__name')
        .annotate(
            total_present=Count(Case(When(is_present=True, then=1))),
            total_absent=Count(Case(When(is_present=False, then=1)))
        )
    )

    # Calculate overall percentages for each student
    for record in attendance_records:
        total_days = record['total_present'] + record['total_absent']
        record['attendance_percentage'] = (
            (record['total_present'] / total_days) * 100 if total_days > 0 else 0
        )

    return render(request, 'Manage/attendance_summary.html', {
        'grade_section': grade_section,
        'term': term,
        'attendance_records': attendance_records,
    })


def student_attendance_report(request, student_id):
    # Get the student
    student = get_object_or_404(Student, id=student_id)

    # Fetch all attendance records for the student
    attendance_records = Attendance.objects.filter(student=student).order_by('date')

    # Total school days and attendance stats
    total_school_days = attendance_records.values('date').distinct().count()
    total_days_present = attendance_records.filter(is_present=True).count()

    # Calculate attendance percentage
    attendance_percentage = (
        (total_days_present / total_school_days) * 100 if total_school_days > 0 else 0
    )

    # Group attendance by date for chart visualization
    daily_attendance = (
        attendance_records
        .values('date')
        .annotate(
            present_count=Count(Case(When(is_present=True, then=1))),
            absent_count=Count(Case(When(is_present=False, then=1))),
        )
    )

    return render(request, 'Manage/student_attendance_report.html', {
        'student': student,
        'attendance_percentage': attendance_percentage,
        'daily_attendance': daily_attendance,
        'total_school_days': total_school_days,
        'total_days_present': total_days_present,
    })


def attendance_chart_data(request, student_id):
    # Get the student
    student = get_object_or_404(Student, id=student_id)

    # Fetch attendance records grouped by date
    daily_attendance = (
        Attendance.objects.filter(student=student)
        .values('date')
        .annotate(
            present_count=Count(Case(When(is_present=True, then=1))),
            absent_count=Count(Case(When(is_present=False, then=1))),
        )
    )

    return JsonResponse(list(daily_attendance), safe=False)


class TimetableCreateView(View):
    def get(self, request):
        form = TimetableForm()
        return render(request, 'performance/add_time_table.html', {'form': form})

    def post(self, request):
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('class-timetable')  # Redirect to a success page or wherever you prefer
        return render(request, 'performance/add_time_table.html', {'form': form})



class TimetableCreateAPIView(generics.CreateAPIView):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer

    def perform_create(self, serializer):
        timetable = serializer.save()

        # Check if the timetable conflicts with an existing one
        overlapping_entries = Timetable.objects.filter(
            grade_section=timetable.grade_section,
            day=timetable.day,
            start_time__lt=timetable.end_time,
            end_time__gt=timetable.start_time
        )
        if overlapping_entries.exists():
            raise ValidationError("This time slot is already occupied.")


#render page for:TimetableAPIView --data
def class_timetable_view(request):
    return render(request, 'performance/time_table.html')

class TimetableAPIView(View):
    def get(self, request, *args, **kwargs):
        try:
            # Optimize query for GradeSections
            grade_sections = list(
                GradeSection.objects.values('id', 'grade__name', 'section__name')
            )

            # Get the selected GradeSection from query params
            selected_grade_section = request.GET.get('grade_section', None)

            if selected_grade_section:
                # Check if the selected grade_section exists
                if not GradeSection.objects.filter(id=selected_grade_section).exists():
                    return JsonResponse({
                        "status": "error",
                        "message": "Invalid grade_section ID provided.",
                        "data": None
                    }, status=400)

                # Optimize timetable query with select_related and prefetch_related
                timetable_entries = Timetable.objects.filter(
                    grade_section_id=selected_grade_section
                ).select_related('subject', 'teacher')
            else:
                timetable_entries = Timetable.objects.none()

            # Days of the week (ordered)
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            # Organize timetable data by day and time
            timetable_data = {day: [] for day in days_of_week}
            unique_times = set()

            for entry in timetable_entries:
                time_range = f"{entry.start_time.strftime('%I:%M %p')} - {entry.end_time.strftime('%I:%M %p')}"
                unique_times.add(time_range)
                timetable_data[entry.day].append({
                    "time": time_range,
                    "subject": entry.subject.name,
                    "teacher": entry.teacher.full_name,
                })

            # Sort unique times for consistent table rows
            unique_times = sorted(unique_times)

            # Success response
            return JsonResponse({
                "status": "success",
                "message": "Timetable fetched successfully.",
                "data": {
                    "grade_sections": grade_sections,
                    "selected_grade_section": selected_grade_section,
                    "timetable_data": timetable_data,
                    "unique_times": unique_times,
                    "days_of_week": days_of_week,
                }
            }, json_dumps_params={'indent': 2})

        except Exception as e:
            # Catch any unexpected errors
            return JsonResponse({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}",
                "data": None
            }, status=500)


class LessonExchangeView(View):
    def get(self, request):
        form = LessonExchangeForm(user=request.user)
        return render(request, 'performance/exchange_lessons.html', {'form': form})

    def post(self, request):
        form = LessonExchangeForm(request.POST, user=request.user)
        if form.is_valid():
            # Handle teacher and admin scenarios dynamically
            if hasattr(request.user, 'teacher'):  # If logged in as a teacher
                teacher_1 = request.user.teacher
                teacher_2 = form.cleaned_data['teacher_2']
            else:  # If logged in as admin
                teacher_1 = form.cleaned_data['teacher_1']
                teacher_2 = form.cleaned_data['teacher_2']

            lesson_1 = form.cleaned_data['lesson_1']
            lesson_2 = form.cleaned_data['lesson_2']

            # Check for time conflicts
            conflict = Timetable.objects.filter(
                day=lesson_1.day,
                start_time__lt=lesson_2.end_time,
                end_time__gt=lesson_1.start_time
            ).exists()

            if conflict:
                messages.warning(request, "The selected lessons conflict. Please choose different lessons.")
                return render(request, 'performance/exchange_lessons.html', {'form': form})

            # Save the lesson exchange request
            exchange_request = form.save(commit=False)
            exchange_request.teacher_1 = teacher_1
            exchange_request.teacher_2 = teacher_2
            exchange_request.conflict = conflict
            exchange_request.save()

            messages.success(request, "Your lesson exchange request has been submitted.")
            return redirect('class-timetable')

        return render(request, 'performance/exchange_lessons.html', {'form': form})





class LessonExchangeApproveView(View):
    def get(self, request, pk):
        try:
            exchange_request = LessonExchangeRequest.objects.get(pk=pk)
        except LessonExchangeRequest.DoesNotExist:
            messages.error(request, "Exchange request not found.")
            return redirect('lesson-exchange-list')

        # Show details of the request (for admin or teacher)
        return render(request, 'performance/approve_exchange.html', {'request': exchange_request})

    def post(self, request, pk):
        try:
            exchange_request = LessonExchangeRequest.objects.get(pk=pk)
        except LessonExchangeRequest.DoesNotExist:
            messages.error(request, "Exchange request not found.")
            return redirect('lesson-exchange-list')

        if 'approve' in request.POST:
            try:
                exchange_request.approve_exchange()
                messages.success(request, "Lesson exchange approved successfully.")
            except ValidationError as e:
                messages.error(request, f"Error: {e}")

        elif 'reject' in request.POST:
            exchange_request.status = 'rejected'
            exchange_request.save()
            messages.success(request, "Lesson exchange rejected.")

        return redirect('lesson-exchange-list')


class LessonExchangeListView(View):
    def get(self, request):
        lesson_exchange_requests = LessonExchangeRequest.objects.filter(status='pending')
        return render(request, 'performance/lesson_exchange_list.html', {'lesson_exchange_requests': lesson_exchange_requests})



def swap_lessons(request, pk):
    exchange_request = get_object_or_404(LessonExchangeRequest, pk=pk)

    if exchange_request.status != 'approved':
        messages.error(request, "This exchange request is not approved yet.")
        return redirect('class-timetable')

    # Swap the lessons
    lesson_1 = exchange_request.lesson_1
    lesson_2 = exchange_request.lesson_2

    # Swap the lessons
    lesson_1.teacher, lesson_2.teacher = lesson_2.teacher, lesson_1.teacher
    lesson_1.save()
    lesson_2.save()

    # Update the exchange request status
    exchange_request.status = 'completed'
    exchange_request.save()

    messages.success(request, "Lessons have been successfully swapped.")
    return redirect('class-timetable')





# class GradeSectionTimetableView(DetailView):
#     model = GradeSection
#     template_name = "performance/time_table.html"
#     context_object_name = "grade_section"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         grade_section = self.get_object()
#
#         timetable_entries = Timetable.objects.filter(grade_section=grade_section).select_related("subject", "teacher")
#         days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#
#         # Organize timetable data
#         timetable_data = {day: [] for day in days_of_week}
#         for entry in timetable_entries:
#             timetable_data[entry.day].append({
#                 "time": f"{entry.start_time.strftime('%I:%M %p')} - {entry.end_time.strftime('%I:%M %p')}",
#                 "subject": entry.subject.name,
#                 "teacher": entry.teacher.full_name,
#             })
#
#         context["timetable_data"] = timetable_data
#         return context


class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name')
    teacher_name = serializers.CharField(source='teacher.name')
    grade_section_name = serializers.CharField(source='grade_section.name')

    class Meta:
        model = Timetable
        fields = ['start_time', 'end_time', 'subject_name', 'teacher_name', 'grade_section_name']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Format the time display
        representation['start_time'] = instance.start_time.strftime('%I:%M %p')
        representation['end_time'] = instance.end_time.strftime('%I:%M %p')

        return representation


class TeacherScheduleAPIView(APIView):
    def get(self, request, teacher_id, date_str):
        try:
            # Convert the date string to a day of the week
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_of_week = date_obj.strftime('%A')  # Get full weekday name (e.g., 'Monday')

            # Fetch teacher's lessons for that day of the week
            teacher = Teacher.objects.get(id=teacher_id)
            lessons = Timetable.objects.filter(
                teacher=teacher,
                day=day_of_week  # Match the 'day' field in the model
            ).order_by('start_time')

            if not lessons.exists():
                return JsonResponse({"message": "No lessons found for the specified date."}, status=404)

            # Prepare lesson data for response
            lesson_data = [
                {
                    'start_time': lesson.start_time.strftime('%H:%M'),
                    'end_time': lesson.end_time.strftime('%H:%M'),
                    'subject_name': lesson.subject.name,
                    'grade_section_name': str(lesson.grade_section.grade),  # Ensure grade is serializable
                }
                for lesson in lessons
            ]

            return JsonResponse(lesson_data, safe=False)

        except Teacher.DoesNotExist:
            return JsonResponse({'error': 'Teacher not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)







def get_grade_sections(request):
    grade_sections = GradeSection.objects.all().values('id', 'grade__name', 'section__name')  # Adjust fields as needed
    return JsonResponse(list(grade_sections), safe=False)



def timetable_create(request):
    return render(request, 'performance/add_time_table.html')


def exam_list(request):
    return render(request, 'performance/exam_list.html')


def time_table(request):
    return render(request, 'performance/time_table.html')


def transport_view(request):
    return render(request, 'performance/transport.html')


def events_view(request):
    return render(request, 'Manage/event.html')


