import json
import logging
from datetime import date, timedelta, datetime

from asgiref.sync import async_to_sync
from chardet.cli.chardetect import description_of
from django.conf import settings
from django.db import transaction
from django.db.models import F, Value, CharField, Case, When, FloatField, QuerySet, Prefetch
from django.db.models.functions import Concat

import requests
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, FieldError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions.datetime import TruncMonth, ExtractYear
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, now
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, TemplateView
from django_daraja.mpesa.core import MpesaClient
from rest_framework import generics, serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import FeePayment, Expense
from apps.management.forms import BookForm, TimetableForm, LessonExchangeForm, ProfileForm, \
    HolidayPresentationForm, FeedbackForm, TermForm, ExamTypeForm, AddResultForm, ClubForm, \
    ReportCardFilterForm
from apps.management.models import Term, ReportCard, SubjectMark, ExamType, \
    Attendance, Timetable, LessonExchangeRequest, HolidayPresentation, Club, Event, ClubEvent, AcademicYear
from apps.management.serializers import EventSerializer, ClubEventSerializer
from apps.schedules.forms import SubjectForm
from apps.schedules.models import Subject
from apps.students.forms import SendSMSForm, SendClassForm, ResultsSMSForm
from apps.students.models import Book, Transaction, Student, Payment, Parent, StudentParent, Grade, GradeSection

# Create your views here.
from django.db.models import Avg, Sum, Count, Q, Window

from apps.students.utils import MobileSasaAPI
from apps.students.views import get_current_term
from apps.teachers.models import Department, Teacher  # Revenue

logger = logging.getLogger(__name__)

from datetime import datetime
from .models import AcademicYear





def manage_terms(request, id=None):
    if id:
        term = get_object_or_404(Term, pk=id)
    else:
        term = None

    if request.method == 'POST':
        form = TermForm(request.POST, instance=term)
        if form.is_valid():
            form.save()
            return redirect('terms')
    else:
        form = TermForm(instance=term)

    terms = Term.objects.all()

    return render(request, 'Manage/term_list.html', {
        'form': form,
        'terms': terms,
        'term': term,
    })


def delete_term(request, id):
    term = get_object_or_404(Term, pk=id)
    term.delete()
    return redirect('terms')


def manage_exam_types(request, id=None):
    """Handles both adding and editing exam types."""

    if id:
        exam_type = get_object_or_404(ExamType, pk=id)  # Fetch exam type for editing
    else:
        exam_type = None  # No ID means it's an add operation

    if request.method == 'POST':
        form = ExamTypeForm(request.POST, instance=exam_type)
        if form.is_valid():
            form.save()
            return redirect('manage_exam_types')  # Stay on the same page
    else:
        form = ExamTypeForm(instance=exam_type)

    exam_types = ExamType.objects.all()  # Get all exam types

    return render(request, 'Manage/exam_types.html', {
        'form': form,
        'exam_types': exam_types,
        'exam_type': exam_type,  # Pass for edit mode check
    })


def delete_exam_type(request, id):
    """deleting an exam type."""
    exam_type = get_object_or_404(ExamType, pk=id)
    exam_type.delete()
    return redirect('manage_exam_types')


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

    return render(request, 'Manage/profile.html',
                  {'profile_form': profile_form, 'profile': profile, 'additional_info': additional_info})


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


def presentation_detail(request, id):
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
    return render(request, 'Manage/manage_users.html', {'users': users})


@staff_member_required
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        user.is_active = not user.is_active  # toggle activation status
        user.save()
        status = "Activated" if user.is_active else "Deactivated"
        messages.success(request, f"User {user.username} has been {status}")
    except User.DoesNotExist:
        messages.error(request, "User not found")
    return redirect('manage_users')


def validate_message_data(report_card):
    """Ensure all required template data exists"""
    validation_errors = []

    if not report_card.total_marks:
        validation_errors.append("Missing total marks")

    if not report_card.subject_marks.exists():
        validation_errors.append("No subject marks found")

    if not report_card.rank:
        validation_errors.append("Rank not calculated")

    return validation_errors


def validate_message_template(template, required_keys):
    """Validate message template contains required placeholders"""
    missing = [key for key in required_keys if f"{{{key}}}" not in template]
    if missing:
        raise ValidationError(f"Missing template keys: {', '.join(missing)}")


def handle_results_sms(request, context):
    api = MobileSasaAPI()
    form_data = request.POST
    required_keys = context['template_keys']['results']

    try:
        term = Term.objects.get(id=form_data.get('term'))
        exam_type = ExamType.objects.get(id=form_data.get('exam_type'))
        message_template = form_data.get('message', '')

        validate_message_template(message_template, required_keys)

        # Get students with complete data
        students = Student.objects.filter(
            status="Active",
            report_cards__term=term,
            report_cards__exam_type=exam_type
        ).prefetch_related(
            Prefetch('report_cards',
                     queryset=ReportCard.objects.filter(term=term, exam_type=exam_type)
                     .select_related('term', 'exam_type')
                     .prefetch_related('subject_marks__subject'),
                     to_attr='relevant_reports'),
            Prefetch('studentparent_set',
                     queryset=StudentParent.objects.select_related('parent')
                     .filter(parent__mobile__isnull=False))
        ).distinct()

        personalized_messages = []
        failed_students = []

        with transaction.atomic():
            for student in students:
                if not student.relevant_reports:
                    continue

                report_card = student.relevant_reports[0]

                # Validate report card data
                data_errors = validate_message_data(report_card)
                if data_errors:
                    failed_students.append({
                        'student': student,
                        'errors': data_errors
                    })
                    continue

                # Format subject results: include subject percentage and subject grade
                subject_lines = []
                for subj in report_card.subject_marks.all():
                    if subj.marks is not None:
                        # Format the subject line to include marks, percentage, and grade.
                        if subj.percentage is not None and subj.subject_grade:
                            line = f"{subj.subject.name}:({subj.percentage:.1f}%, {subj.subject_grade})"
                        else:
                            line = f"{subj.subject.name}: {subj.marks}"
                        subject_lines.append(line)

                if not subject_lines:
                    continue  # Skip students with no valid marks

                parents = {sp.parent for sp in student.studentparent_set.all()}

                for parent in parents:
                    try:
                        message = message_template.format(
                            parent_name=parent.first_name,
                            student_name=student.first_name,
                            student_class=f"{student.grade.grade.name} {student.grade.section.name}",
                            total_marks=report_card.total_marks,
                            rank=report_card.rank,
                            subject_results=", ".join(subject_lines),
                            term=f"{term.name} {term.year}",
                            exam_type=exam_type.name,
                            average_marks=report_card.average_marks,
                            overall_grade=report_card.grade
                        )
                        personalized_messages.append({
                            "phone": parent.mobile,
                            "message": message
                        })
                    except KeyError as e:
                        logger.error(f"Missing template key: {str(e)}")
                        raise
                    except Exception as e:
                        logger.error(f"Format error for {parent}: {str(e)}")
                        continue

        if personalized_messages:
            success_count, errors = api.send_bulk_personalized_sms(personalized_messages)

            # Prepare result message
            msg = f"Successfully sent to {success_count} parents"
            if failed_students:
                msg += f" ({len(failed_students)} students skipped due to incomplete data)"
            messages.success(request, msg)

            if errors:
                request.session['sms_errors'] = [
                    f"Error {e.get('code')}: {e.get('message')}" if isinstance(e, dict) else str(e)
                    for e in errors[:5]  # Show first 5 errors
                ]
                messages.warning(request, f"{len(errors)} message chunks failed. See details below.")
        else:
            messages.warning(request,
                             "No valid recipients found. Reasons:", extra_tags='recipient_warning')
            messages.info(request,
                          "- Students must have complete report cards", extra_tags='recipient_warning')
            messages.info(request,
                          "- Parents must have valid mobile numbers", extra_tags='recipient_warning')

        # Log data validation failures
        if failed_students:
            logger.warning(f"Failed students: {len(failed_students)}")
            for fs in failed_students:
                logger.warning(f"Student {fs['student'].id} errors: {', '.join(fs['errors'])}")

    except (Term.DoesNotExist, ExamType.DoesNotExist) as e:
        messages.error(request, "Invalid term or exam type selected")
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect('unified_sms')


def recipient_count(request):
    sms_type = request.GET.get('type')

    if sms_type == 'class':
        # Use the GET parameter if provided; otherwise, default to all grade sections.
        grade_sections_param = request.GET.get('grade_sections')
        if grade_sections_param:
            # Expecting a comma-separated list, e.g., "3,5,7"
            grade_section_ids = grade_sections_param.split(',')
        else:
            grade_section_ids = list(
                GradeSection.objects.all().values_list('id', flat=True)
            )

        # Count StudentParent records where:
        # - The student's grade is in the selected grade sections.
        # - The student is active.
        # - The linked parent has a valid mobile number.
        count = StudentParent.objects.filter(
            student__grade__id__in=grade_section_ids,
            student__status="Active",
            parent__mobile__isnull=False
        ).count()

    elif sms_type == 'results':
        term = request.GET.get('term')
        exam_type = request.GET.get('exam_type')

        # Count StudentParent records based on the report card criteria and active student status.
        count = StudentParent.objects.filter(
            student__report_cards__term_id=term,
            student__report_cards__exam_type_id=exam_type,
            student__status="Active"
        ).count()

    else:
        # For bulk SMS, count StudentParent records for active students with valid mobile numbers.
        count = StudentParent.objects.filter(
            student__status="Active",
            parent__mobile__isnull=False
        ).count()

    return JsonResponse({'count': count})


def validate_parent_relationships(student):
    """Check if student has valid parent relationships"""
    return StudentParent.objects.filter(student=student).exists()


def validate_parent_mobile(student):
    """Check if at least one parent has a mobile number"""
    return StudentParent.objects.filter(
        student=student,
        parent__mobile__isnull=False
    ).exists()


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def unified_sms_view(request):
    context = {
        'terms': Term.objects.all(),
        'exam_types': ExamType.objects.all(),
        'grade_sections': GradeSection.objects.select_related('grade', 'section')
        .order_by('grade__level', 'section__name'),
        'template_keys': {
            'results': {'parent_name', 'student_name', 'student_class',
                       'average_marks','overall_grade', 'rank', 'subject_results', 'term', 'exam_type'},
            'class': {'class_name', 'teacher_name', 'student_name'},
            'bulk': set()
        }
    }

    if request.method == "POST":
        sms_type = request.POST.get('sms_type', 'bulk')
        try:
            if sms_type == 'results':
                return handle_results_sms(request, context)
            elif sms_type == 'class':
                return handle_class_sms(request, context)
            elif sms_type == 'bulk':
                return handle_bulk_sms(request, context)
            else:
                messages.error(request, "Invalid SMS type selected")
                return redirect('unified_sms')
        except Exception as e:
            logger.error(f"SMS Error: {str(e)}", exc_info=True)
            messages.error(request, f"Operation failed: {str(e)}")
            return redirect('unified_sms')

    # GET request - initialize counts.
    # For bulk SMS, count distinct Parent objects that have a valid mobile number
    # and are linked to at least one active student.
    bulk_count = Parent.objects.filter(
        mobile__isnull=False,
        students__status="Active"
    ).distinct().count()

    context.update({
        'bulk_count': bulk_count,
        'grade_section_count': context['grade_sections'].count(),
        'term_count': context['terms'].count(),
        'sms_type': request.GET.get('type', 'bulk'),
        'exam_type_count': context['exam_types'].count()
    })

    return render(request, 'Manage/send_sms.html', context)


@login_required
def handle_class_sms(request, context):
    api = MobileSasaAPI()
    # Get the list of grade section IDs from the form submission.
    grade_section_ids = request.POST.getlist('grade_sections')
    # Retrieve the SMS message from the form.
    message = request.POST.get('message')

    try:
        # Validate message existence and length.
        if not message:
            raise ValidationError("Message is required.")
        if len(message) > 160:
            raise ValidationError("Message exceeds 160 character limit.")

        # Ensure that at least one class section is selected.
        if not grade_section_ids:
            raise ValidationError("Please select at least one class section.")

        # Query for parents whose children are in the selected grade sections,
        # whose students are Active, and who have a valid mobile number.
        parents = Parent.objects.filter(
            studentparent__student__grade__id__in=grade_section_ids,
            studentparent__student__status="Active",
            mobile__isnull=False
        ).distinct()

        # If no parents are found, display a warning and redirect.
        if not parents.exists():
            messages.warning(request, "No parents found for selected classes.")
            return redirect('unified_sms')

        # Build a list of phone numbers from the parent's mobile field.
        phone_numbers = [str(parent.mobile) for parent in parents if parent.mobile]
        if not phone_numbers:
            messages.warning(request, "Selected parents have no valid phone numbers.")
            return redirect('unified_sms')

        # Send the bulk SMS using the updated SMSHandler.send_bulk_sms.
        # This function now sends the message individually for each phone number.
        success_count, errors = api.send_bulk_sms(message, phone_numbers)

        # Show a success message if any messages were sent.
        if success_count:
            messages.success(request, f"Sent SMS to {success_count} out of {len(phone_numbers)} parents.")
        # Show an error message if there were any failures.
        if errors:
            # Optionally combine error messages into one string.
            error_details = "; ".join([error.get('message', 'Unknown error') for error in errors])
            messages.error(request, f"Failed to send SMS to {len(errors)} recipients: {error_details}")

    except ValidationError as e:
        # Catch any validation errors and display them.
        messages.error(request, str(e))

    # Redirect back to the unified SMS view.
    return redirect('unified_sms')


@login_required
def handle_bulk_sms(request, context):
    api = MobileSasaAPI()
    message = request.POST.get('message')

    try:
        if len(message) > 160:
            raise ValidationError("Message exceeds 160 character limit")

        # Stream StudentParent objects whose student is Active and whose parent has a valid mobile number.
        parents_iterator = StudentParent.objects.filter(
            student__status="Active",
            parent__mobile__isnull=False
        ).iterator()

        # Build the phone number list from each StudentParent's parent.
        phone_numbers = [str(sp.parent.mobile) for sp in parents_iterator]

        if not phone_numbers:
            messages.warning(request, "No parents with valid numbers found")
            return redirect('unified_sms')

        # Send the bulk SMS using the updated SMSHandler.send_bulk_sms.
        success_count, errors = api.send_bulk_sms(message, phone_numbers)

        if success_count:
            messages.success(request, f"Sent to {success_count} parents")
        if errors:
            messages.error(request, f"Failed to send {len(errors)} messages")

    except ValidationError as e:
        messages.error(request, str(e))

    return redirect('unified_sms')


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
    results = SubjectMark.objects.select_related('student', 'teacher_subject__teacher', 'teacher_subject__subject',
                                                 'term')
    return render(request, 'performance/results.html', {'results': results})


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

# filter by grade/section


# def performance_filter_view(request):
#     if request.method == "POST":
#         form = PerformanceFilterForm(request.POST)
#         if form.is_valid():
#             grade_id = form.cleaned_data.get('grade')
#             grade_section_id = form.cleaned_data.get('grade_section')
#             term_id = form.cleaned_data['term'].id
#             exam_type_id = form.cleaned_data['exam_type'].id
#
#             # Redirect based on the selection
#             if grade_id:
#                 return redirect(reverse('view_results_table', args=[grade_id.id, term_id, exam_type_id]))
#             elif grade_section_id:
#                 return redirect(
#                     reverse('view_results_table_section', args=[grade_section_id.id, term_id, exam_type_id]))
#
#     else:
#         form = PerformanceFilterForm()
#
#     return render(request, 'performance/class_results_view.html', {'form': form})


# Filter Results View to add
def filter_results(request):
    grades = GradeSection.objects.all()
    terms = Term.objects.all()
    subjects = Subject.objects.all()
    exam_types = ExamType.objects.all()

    context = {
        'grades': grades,
        'terms': terms,
        'subjects': subjects,
        'exam_types': exam_types,
    }

    return render(request, 'performance/filter_form.html', context)


# Add or Update Results Table View
# def add_results_table(request):
#     """Handles adding student subject marks and creating/updating report cards."""
#
#     # Get filtering parameters from request
#     grade_id = request.GET.get('grade_id')
#     term_id = request.GET.get('term_id')
#     subject_id = request.GET.get('subject_id')
#     exam_type_id = request.GET.get('exam_type_id')
#
#     # Validate required parameters
#     if not all([grade_id, term_id, subject_id, exam_type_id]):
#         messages.error(request, "Missing required parameters. Please ensure all fields are selected.")
#         return render(request, 'Manage/errors/500.html', {'message': 'Missing required parameters.'})
#
#     # Fetch related objects
#     selected_grade = get_object_or_404(GradeSection, id=grade_id)
#     selected_term = get_object_or_404(Term, id=term_id)
#     selected_subject = get_object_or_404(Subject, id=subject_id)
#     selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)
#
#     students = Student.objects.filter(grade=selected_grade)
#     max_score = float(request.POST.get('max_score', 100) or 100)
#
#     if request.method == 'POST':
#         try:
#             with transaction.atomic():
#                 # Fetch existing report cards in bulk
#                 report_cards = {
#                     rc.student_id: rc for rc in ReportCard.objects.filter(
#                         student__in=students, term=selected_term, exam_type=selected_exam_type
#                     )
#                 }
#
#                 # Process marks input for each student
#                 for student in students:
#                     mark_value = request.POST.get(f'marks_{student.id}', '').strip()
#
#                     if not mark_value:  # Skip empty marks
#                         continue
#
#                     try:
#                         mark_value = float(mark_value)
#                     except ValueError:
#                         messages.warning(request, f"Invalid marks input for {student.name}. Skipping entry.")
#                         continue  # Skip invalid input
#
#                     # Get or create the student's report card
#                     report_card = report_cards.get(student.id)
#                     if not report_card:
#                         report_card = ReportCard.objects.create(
#                             student=student, term=selected_term, exam_type=selected_exam_type, year=selected_term.year
#                         )
#                         report_cards[student.id] = report_card
#
#                     # Update or create the SubjectMark entry
#                     SubjectMark.objects.update_or_create(
#                         report_card=report_card,
#                         subject=selected_subject,
#                         defaults={'marks': mark_value, 'max_score': max_score}
#                     )
#
#             messages.success(request, "Results added successfully!")
#             return HttpResponseRedirect(
#                 f'/management/view_results/?subject_id={subject_id}&term_id={term_id}&exam_type_id={exam_type_id}'
#             )
#
#         except Exception as e:
#             logger.error(f"Error in add_results_table: {e}", exc_info=True)
#             messages.error(request, "An error occurred while processing results.")
#             return render(request, 'Manage/errors/500.html', {'message': 'An error occurred while processing results.'})
#
#     # Fetch existing marks efficiently
#     existing_marks = dict(
#         SubjectMark.objects.filter(
#             report_card__student__in=students,
#             report_card__term=selected_term,
#             report_card__exam_type=selected_exam_type,
#             subject=selected_subject
#         ).values_list('report_card__student_id', 'marks')
#     ) if students.exists() else {}
#
#     # Prepare context for template rendering
#     context = {
#         'selected_grade': selected_grade,
#         'selected_term': selected_term,
#         'selected_subject': selected_subject,
#         'selected_exam_type': selected_exam_type,
#         'students': students,
#         'max_score': max_score,
#         'existing_marks': existing_marks,
#     }
#
#     return render(request, 'performance/add_results_table.html', context)


def view_subject_results(request):
    # Get the filtering parameters from the GET request
    subject_id = request.GET.get('subject_id')
    term_id = request.GET.get('term_id')
    exam_type_id = request.GET.get('exam_type_id')

    # Initialize selected filters
    selected_subject = None
    selected_term = None
    selected_exam_type = None

    # Check if IDs are provided and fetch the corresponding objects
    try:
        if subject_id:
            selected_subject = Subject.objects.get(id=subject_id)

        if term_id:
            selected_term = Term.objects.get(id=term_id)

        if exam_type_id:
            selected_exam_type = ExamType.objects.get(id=exam_type_id)
    except (Subject.DoesNotExist, Term.DoesNotExist, ExamType.DoesNotExist) as e:
        print(f"Error: {e}")
        return HttpResponse("Invalid selection parameters", status=400)

    # Fetch all students (or filter by grade if needed)
    students = Student.objects.all()

    # Create a dictionary to store marks for each student
    student_marks = {}

    # Get the marks for each student based on the selected subject, term, and exam type
    for student in students:
        try:
            # Fetch the corresponding SubjectMark for the student and subject filters
            subject_mark = SubjectMark.objects.get(
                report_card__student=student,  # Ensure we're referencing through report_card's student
                subject=selected_subject,
                report_card__term=selected_term,
                report_card__exam_type=selected_exam_type
            )
            student_marks[student.id] = subject_mark.marks  # Store the marks in the dictionary
        except SubjectMark.DoesNotExist:
            student_marks[student.id] = None  # No marks found for this student

    # Pass the necessary context to the template
    context = {
        'students': students,
        'selected_subject': selected_subject,
        'selected_term': selected_term,
        'selected_exam_type': selected_exam_type,
        'student_marks': student_marks,  # Provide the student_marks dictionary to the template
    }

    return render(request, 'performance/subject_results.html', context)


def add_results_table(request):
    """Handles adding student subject marks and updating report cards."""

    # Get filtering parameters
    grade_id = request.GET.get('grade_id')
    term_id = request.GET.get('term_id')
    subject_id = request.GET.get('subject_id')
    exam_type_id = request.GET.get('exam_type_id')

    if not all([grade_id, term_id, subject_id, exam_type_id]):
        messages.error(request, "Missing required parameters. Please select all fields.")
        return render(request, 'Manage/errors/500.html', {'message': 'Missing required parameters.'})

    # Fetch related objects
    selected_grade = get_object_or_404(GradeSection, id=grade_id)
    selected_term = get_object_or_404(Term, id=term_id)
    selected_subject = get_object_or_404(Subject, id=subject_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    students = Student.objects.filter(grade=selected_grade)
    max_score = float(request.POST.get('max_score', 100) or 100)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                report_cards = {
                    rc.student_id: rc for rc in ReportCard.objects.filter(
                        student__in=students, term=selected_term, exam_type=selected_exam_type
                    )
                }

                marks_entered = False  # Track if any marks were actually entered

                for student in students:
                    mark_value = request.POST.get(f'marks_{student.id}', '').strip()

                    if not mark_value:  # Skip empty marks
                        continue

                    try:
                        mark_value = float(mark_value)
                        marks_entered = True  # At least one mark was entered
                    except ValueError:
                        messages.warning(request, f"Invalid marks input for {student.name}. Skipping entry.")
                        continue

                    # Get or create the student's report card
                    report_card = report_cards.get(student.id)
                    if not report_card:
                        report_card = ReportCard.objects.create(
                            student=student, term=selected_term, exam_type=selected_exam_type, year=selected_term.year
                        )
                        report_cards[student.id] = report_card

                    # Update or create the SubjectMark entry
                    SubjectMark.objects.update_or_create(
                        report_card=report_card,
                        subject=selected_subject,
                        defaults={'marks': mark_value, 'max_score': max_score}
                    )

            if marks_entered:
                messages.success(request, "Results added successfully!")
                return HttpResponseRedirect(
                    reverse('view_results_table',
                            kwargs={'grade_section_id': grade_id, 'term_id': term_id, 'exam_type_id': exam_type_id})
                )
            else:
                messages.warning(request, "No marks were entered. Please enter marks before submitting.")

        except Exception as e:
            logger.error(f"Error in add_results_table: {e}", exc_info=True)
            messages.error(request, "An error occurred while processing results.")

    # Fetch existing marks efficiently
    existing_marks = dict(
        SubjectMark.objects.filter(
            report_card__student__in=students,
            report_card__term=selected_term,
            report_card__exam_type=selected_exam_type,
            subject=selected_subject
        ).values_list('report_card__student_id', 'marks')
    ) if students.exists() else {}

    context = {
        'selected_grade': selected_grade,
        'selected_term': selected_term,
        'selected_subject': selected_subject,
        'selected_exam_type': selected_exam_type,
        'students': students,
        'max_score': max_score,
        'existing_marks': existing_marks,
    }

    return render(request, 'performance/add_results_table.html', context)


# def view_results_table(request, grade_section_id, term_id=None, exam_type_id=None):
#     grade_section = get_object_or_404(GradeSection, id=grade_section_id)
#     grade = grade_section.grade
#     students = Student.objects.filter(grade=grade_section)
#     subjects = Subject.objects.filter(grade=grade_section.grade)
#
#     # Determine if it's a GradeSection or Grade
#     if isinstance(grade_section, GradeSection):
#         selected_class = grade_section
#     else:
#         selected_class = grade
#
#     # Fetch the selected term and exam type
#     selected_term = get_object_or_404(Term, id=term_id) if term_id else None
#     selected_exam_type = get_object_or_404(ExamType, id=exam_type_id) if exam_type_id else None
#
#     # Fetch report cards with optimized queries
#     report_cards = ReportCard.objects.filter(student__in=students, term_id=term_id, exam_type_id=exam_type_id).annotate(
#         annotated_total_marks=F('total_marks'),
#         annotated_grade=F('grade')
#     )
#
#     # Prepare student data
#     student_data = []
#     for report in report_cards:
#         student_marks = {}
#         for subject in subjects:
#             mark = SubjectMark.objects.filter(report_card=report, subject=subject).first()
#             student_marks[subject.id] = mark.marks if mark else None
#
#         student_data.append({
#             'id': report.student.id,
#             'name': f"{report.student.first_name} {report.student.last_name}",
#             'admission_number': report.student.admission_number,
#             'total_marks': report.annotated_total_marks,
#             'grade': report.annotated_grade,
#             'student_marks': student_marks,
#             'rank': report.student.report_cards.filter(term_id=term_id,
#                                                        exam_type_id=exam_type_id).first().student_rank()
#             if report.student.report_cards.exists() else None,
#         })
#
#     # Rank students based on total marks
#     student_data.sort(key=lambda x: x['total_marks'], reverse=True)
#     for rank, student in enumerate(student_data, 1):
#         student['rank'] = rank
#
#     context = {
#         'subjects': subjects,
#         'student_data': student_data,
#         'selected_class': selected_class,
#         'selected_term': selected_term,
#         'selected_exam_type': selected_exam_type,
#     }
#
#     return render(request, 'performance/view_results_table.html', context)


def report_card_view(request):
    form = ReportCardFilterForm(request.GET or None)
    report_card_data = []
    subjects = []

    # Initialize values to None to avoid reference errors
    grade = None
    grade_section = None
    term = None
    exam_type = None

    if form.is_valid():
        exam_type = form.cleaned_data.get('exam_type')
        term = form.cleaned_data.get('term')
        grade = form.cleaned_data.get('grade')
        grade_section = form.cleaned_data.get('grade_section')

        # Determine students based on grade or grade_section
        if grade:
            grade_sections = GradeSection.objects.filter(grade=grade)
            students = Student.objects.filter(grade__in=grade_sections)
            filter_by_grade = True  # Rank by entire grade
        else:
            students = Student.objects.filter(grade=grade_section)
            filter_by_grade = False  # Rank by section

        # Fetch report cards with related data
        report_cards = ReportCard.objects.filter(
            student__in=students,
            exam_type=exam_type,
            term=term
        ).select_related('student').prefetch_related(
            Prefetch('subject_marks', queryset=SubjectMark.objects.select_related('subject'))
        ).order_by('rank')

        # Collect unique subjects from all report cards
        subjects = Subject.objects.filter(
            subject_marks__report_card__in=report_cards
        ).distinct().order_by('name')

        # Prepare data for each report card
        for rc in report_cards:
            subject_dict = {sm.subject: (sm.percentage, sm.subject_grade) for sm in rc.subject_marks.all()}
            subject_list = []
            for subj in subjects:
                data = subject_dict.get(subj)
                subject_list.append({
                                        'percentage': data[0] if data else None,
                                        'grade': data[1] if data else '-'
                                    } if data else None)
            report_card_data.append({
                'student': rc.student,
                'subjects': subject_list,
                'total': rc.total_marks,
                'average': rc.average_marks,
                'grade': rc.grade,
                'rank': rc.student_rank(filter_by_grade)
            })

    #Passrequired data to the template
    return render(request, 'performance/view_results_table.html', {
        'form': form,
        'subjects': subjects,
        'report_card_data': report_card_data,
        'grade_section': grade_section,
        'grade': grade,
        'selected_term': term,
        'selected_exam_type': exam_type,
    })


# def performance_filter_view(request):
#     if request.method == 'POST':
#         form = PerformanceFilterForm(request.POST)
#         if form.is_valid():
#             grade = form.cleaned_data.get('grade')
#             grade_section = form.cleaned_data.get('grade_section')
#             term_id = form.cleaned_data['term'].id
#             exam_type_id = form.cleaned_data['exam_type'].id
#
#             # Ensure only one of grade or grade_section is selected
#             if grade and grade_section:
#                 form.add_error(None, 'You cannot select both Grade and Grade Section at the same time.')
#                 return render(request, 'performance/class_results_view.html', {'form': form})
#
#             if not grade and not grade_section:
#                 form.add_error(None, 'You must select either a Grade or a Grade Section.')
#                 return render(request, 'performance/class_results_view.html', {'form': form})
#
#             # Redirect based on selection
#             if grade_section:
#                 return redirect(reverse('view_results_table_with_section', kwargs={
#                     'term_id': term_id,
#                     'exam_type_id': exam_type_id,
#                     'grade_section_id': grade_section.id
#                 }))
#             else:
#                 return redirect(reverse('view_results_table', kwargs={
#                     'term_id': term_id,
#                     'exam_type_id': exam_type_id,
#                     'grade_id': grade.id
#                 }))
#
#     else:
#         form = PerformanceFilterForm()
#
#     return render(request, '', {'form': form})


def view_results_table(request, term_id, exam_type_id, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    students = Student.objects.filter(grade=grade)

    context = {
        'students': students,
        'term_id': term_id,
        'exam_type_id': exam_type_id,
        'grade': grade
    }
    return render(request, 'performance/view_results_table.html', context)


def view_results_table_with_section(request, term_id, exam_type_id, grade_section_id):
    grade_section = get_object_or_404(GradeSection, id=grade_section_id)
    students = Student.objects.filter(grade=grade_section.grade, grade_section=grade_section)

    context = {
        'students': students,
        'term_id': term_id,
        'exam_type_id': exam_type_id,
        'grade_section': grade_section
    }
    return render(request, 'performance/view_results_table.html', context)


def process_student_data(students, report_cards, subjects):
    student_data = []

    for student in students:
        report_card = report_cards.filter(student=student).first()

        student_marks = {
            subject.id: SubjectMark.objects.filter(report_card__student=student, subject=subject).first().marks
            if SubjectMark.objects.filter(report_card__student=student, subject=subject).exists() else None
            for subject in subjects
        }

        student_data.append({
            'rank': report_card.rank if report_card else None,
            'admission_number': student.admission_number,
            'name': student.first_name,
            'student_marks': student_marks,
            'total_marks': report_card.total_marks if report_card else None,
            'grade': report_card.grade if report_card else None,
        })

    return student_data


# def view_results_table(request, grade_id, term_id, exam_type_id, subject_id):
#     # Get the GradeSection based on grade_id
#     selected_grade_section = get_object_or_404(GradeSection, id=grade_id)
#
#     # Fetch the associated Grade from the GradeSection
#     selected_class = selected_grade_section.grade
#
#     # Get selected term, exam type, and subject
#     selected_term = get_object_or_404(Term, id=term_id)
#     selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)
#
#     # Fetch all subjects that the students are taking
#     subjects = Subject.objects.all()  # You can modify this to filter subjects by grade if needed
#
#     # Fetch all GradeSections for the selected grade (e.g., all sections for Grade1)
#     grade_sections = GradeSection.objects.filter(grade=selected_class)
#
#     # Fetch all students from the selected grade's sections
#     students = Student.objects.filter(grade__in=grade_sections)
#
#     student_data = []
#     for student in students:
#         marks = []
#         total_marks = 0
#
#         # Get marks for each subject the student is taking
#         for subject in subjects:
#             subject_mark = SubjectMark.objects.filter(
#                 student=student,
#                 subject=subject,
#                 term=selected_term,
#                 exam_type=selected_exam_type
#             ).first()
#
#             # If marks are available, calculate percentage and add to the list
#             if subject_mark and subject_mark.marks != "-":
#                 # Calculate the percentage if marks are available
#                 percentage = round((subject_mark.marks / subject_mark.max_score) * 100)
#                 marks.append(f"{percentage}%")  # Append percentage with % symbol
#                 total_marks += percentage  # Add percentage to total_marks for rank calculation
#             else:
#                 marks.append("-")
#
#         student_data.append({
#             'admission_number': student.admission_number,
#             'name': f"{student.first_name} {student.last_name}",
#             'marks': marks,
#             'total_marks': total_marks,
#         })
#
#     # Sort by total_marks in descending order
#     student_data = sorted(student_data, key=lambda x: x['total_marks'], reverse=True)
#
#     # Add ranking
#     for index, student in enumerate(student_data):
#         student['rank'] = index + 1
#
#     context = {
#         'selected_class': selected_class,
#         'selected_term': selected_term,
#         'selected_exam_type': selected_exam_type,
#         'subjects': subjects,
#         'grade_sections': grade_sections,
#         'student_data': student_data,
#     }
#
#     return render(request, 'performance/view_results_table.html', context)


# def report_card_view(request, student_id, term_id):
#     student = get_object_or_404(Student, id=student_id)
#     term = get_object_or_404(Term, id=term_id)
#
#     # Fetch or create the report card for the student and term
#     report_card, created = ReportCard.objects.get_or_create(student=student, term=term)
#
#     # Calculate total marks and rank
#     total_marks = report_card.total_marks()  # Assuming `total_marks` method is defined in your ReportCard model
#     rank = report_card.student_rank()  # Assuming `student_rank` method is defined in your ReportCard model
#
#     # Fetch subject marks for the student in the given term
#     subject_marks = SubjectMark.objects.filter(student=student, term=term)
#
#     # Prepare subject-wise marks for display
#     subject_marks_data = []
#     for subject_mark in subject_marks:
#         subject_marks_data.append({
#             'subject': subject_mark.subject.name,
#             'marks': subject_mark.marks,
#         })
#
#     # Return the data as JSON to be used dynamically
#     return JsonResponse({
#         'total_marks': total_marks,
#         'rank': rank,
#         'subject_marks': subject_marks_data,  # Include subject-wise marks
#     })


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
# @login_required
# def grade_performance_view(request, grade_id, term_id):
#     grade = G.objects.get(id=grade_id)
#     term = Term.objects.get(id=term_id)
#     performances = Performance.objects.filter(
#         student__grade=grade,
#         term=term
#     ).select_related("student", "subject")
#
#     # Aggregate data
#     student_performance = (
#         performances.values("student__first_name", "student__last_name")
#         .annotate(
#             average_percentage=Avg("marks") / Avg("total_marks") * 100,
#             total_marks=Avg("total_marks"),
#             total_obtained_marks=Avg("marks"),
#         )
#     )
#
#     context = {
#         "grade": grade,
#         "term": term,
#         "student_performance": student_performance,
#     }
#     return render(request, "performance/student_performance.html", context)


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
    # Fetch the Teacher instance using the logged-in user
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get the grade section assigned to the teacher
    grade_section = get_object_or_404(GradeSection, id=grade_section_id, class_teacher=teacher)

    # Fetch the list of students in the GradeSection
    students = Student.objects.filter(grade=grade_section)

    # Fetch the term object
    term = get_object_or_404(Term, id=term_id)

    # If attendance is being submitted
    if request.method == 'POST':
        updated_students = []  # Track students whose attendance was updated
        for student in students:
            # Get attendance status and reason for absence
            is_present = request.POST.get(f'present_{student.id}', 'off') == 'on'
            absence_reason = request.POST.get(f'absence_reason_{student.id}', '')

            # Save attendance
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                section=grade_section,
                teacher=teacher,  # ✅ Now saving Teacher instance
                date=now().date(),  # Ensure attendance is recorded for today
                term=term,
                defaults={'is_present': is_present, 'absence_reason': absence_reason}
            )

            # Track students whose attendance was updated
            updated_students.append(student.first_name)

        # ✅ Display confirmation message
        if updated_students:
            messages.success(request, f"Attendance updated successfully for {len(updated_students)} students.")

        # Redirect to confirmation or summary page
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
        .values('student__id', 'student__first_name')
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


#
# # class TimetableCreateAPIView(generics.CreateAPIView):
# #     queryset = Timetable.objects.all()
# #     serializer_class = TimetableSerializer
# #
# #     def perform_create(self, serializer):
# #         timetable = serializer.save()
# #
# #         # Check if the timetable conflicts with an existing one
# #         overlapping_entries = Timetable.objects.filter(
# #             grade_section=timetable.grade_section,
# #             day=timetable.day,
# #             start_time__lt=timetable.end_time,
# #             end_time__gt=timetable.start_time
# #         )
# #         if overlapping_entries.exists():
# #             raise ValidationError("This time slot is already occupied.")
# #
#
# # render page for:TimetableAPIView --data
# def class_timetable_view(request):
#     return render(request, 'performance/time_table.html')


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
        return render(request, 'performance/lesson_exchange_list.html',
                      {'lesson_exchange_requests': lesson_exchange_requests})


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


@api_view(['GET', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def event_list(request):
    logger.info(f"Request received: {request.build_absolute_uri()} from {request.META.get('HTTP_REFERER')}")

    event_type = request.GET.get('event_type', 'all')

    # Retrieve events based on event type filter
    events = Event.objects.all() if event_type in ['general', 'all'] else Event.objects.none()
    club_events = ClubEvent.objects.all() if event_type in ['club', 'all'] else ClubEvent.objects.none()

    event_serializer = EventSerializer(events, many=True)
    club_event_serializer = ClubEventSerializer(club_events, many=True)

    # Format events properly for FullCalendar
    all_events = [
        {
            'id': event['id'],
            'title': event['name'],
            'start': f"{event['date']}T{event.get('time', '00:00')}",
            'description': event.get('description', ''),
            'event_type': event['event_type'],
            'className': 'bg-info'
        }
        for event in event_serializer.data
    ]

    all_events.extend([
        {
            'id': club_event['id'],
            'title': f"{club_event['title']} ({club_event['club_name']})",
            'start': f"{club_event['event_date']}T{club_event.get('event_time', '00:00')}",
            'description': club_event.get('description', ''),
            'event_type': 'Club Event',
            'className': 'bg-success'
        }
        for club_event in club_event_serializer.data
    ])

    return Response(all_events, status=status.HTTP_200_OK)


# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def event_list(request):
#     if not request.user.is_authenticated:
#         return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
#
#     event_type = request.GET.get('event_type', 'all')
#
#     # Ensure proper fetching logic
#     events = Event.objects.all() if event_type in ['general', 'all'] else Event.objects.none()
#     club_events = ClubEvent.objects.all() if event_type in ['club', 'all'] else ClubEvent.objects.none()
#
#     event_serializer = EventSerializer(events, many=True)
#     club_event_serializer = ClubEventSerializer(club_events, many=True)
#
#     all_events = [
#         {
#             'id': event['id'],
#             'title': event['name'],
#             'start': event['date'] + ('T' + event.get('time', '') if event.get('time') else ''),
#             'description': event.get('description', ''),
#             'event_type': event['event_type'],
#             'className': 'bg-info'
#         }
#         for event in event_serializer.data
#     ]
#
#     all_events.extend([
#         {
#             'id': club_event['id'],
#             'title': club_event['title'] + f" ({club_event['club_name']})",
#             'start': club_event['event_date'] + ('T' + club_event.get('event_time', '') if club_event.get('event_time') else ''),
#             'description': club_event.get('description', ''),
#             'event_type': 'Club Event',
#             'className': 'bg-success'
#         }
#         for club_event in club_event_serializer.data
#     ])
#
#     return Response(all_events, status=status.HTTP_200_OK)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.user != event.created_by and not request.user.is_staff:
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        event.delete()
        return Response({"message": "Event deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class IsAdminOrClubLeader(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            event_type = request.data.get("event_type")
            if event_type == "general" and not request.user.is_staff:
                return False
            if event_type == "club" and not request.user.groups.filter(name="Club Leader").exists():
                return False
        return True


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_event(request):
    data = request.data
    event_type = data.get("event_type")

    serializer = EventSerializer(data=data) if event_type == "general" else ClubEventSerializer(data=data)

    if serializer.is_valid():
        event = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def create_club(request):
    if request.method == "POST":
        form = ClubForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": form.errors})
    return JsonResponse({"success": False, "error": "Invalid request"})


def club_list(request):
    clubs = Club.objects.all()
    teachers = Teacher.objects.all()  # for dropdown
    return render(request, 'schedules/club_list.html', {'clubs': clubs, 'teachers': teachers})


def edit_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    if request.method == "POST":
        form = ClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": form.errors})
    return JsonResponse({"success": False, "error": "Invalid request"})


# View to handle deleting a club
def delete_club(request, club_id):
    if request.method == "POST":
        club = get_object_or_404(Club, id=club_id)
        club.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})


def club_detail(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    return render(request, 'schedules/club_detail.html', {'club': club})


@csrf_exempt
def assign_teachers(request, club_id):
    if request.method == "POST":
        data = json.loads(request.body)
        teacher_ids = data.get("teacher_ids", [])
        club = get_object_or_404(Club, id=club_id)

        teachers = Teacher.objects.filter(id__in=teacher_ids)
        club.teachers.set(teachers)  # Assign multiple teachers

        return JsonResponse({"success": True, "message": "Teachers assigned successfully"})

    return JsonResponse({"success": False, "error": "Invalid request"})


@csrf_exempt  # Only for testing, use CSRF token in production
def add_member(request, club_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')

            if not student_id:
                return JsonResponse({'status': 'error', 'message': 'Student ID is required'}, status=400)

            # ✅ Retrieve the club and student
            try:
                club = Club.objects.get(id=club_id)
            except Club.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Club not found'}, status=404)

            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Student not found'}, status=404)

            # ✅ Add student to the club and save it to the database
            club.members.add(student)
            club.save()  # Ensures the update is committed

            # ✅ Debugging: Check if the student is actually added
            if student in club.members.all():
                return JsonResponse(
                    {'status': 'success', 'message': f'Student {student.name} added to {club.name} successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to add student to club'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def search_student(request):
    query = request.GET.get('q', '').strip()

    if query:
        try:
            # Use Q objects for better readability
            students = Student.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(admission_number__icontains=query)
            )

            student_list = [
                {'id': student.id, 'name': f"{student.first_name} {student.last_name}",
                 'admission_no': student.admission_number}
                for student in students
            ]

            return JsonResponse({'students': student_list})
        except FieldError as e:
            print("FieldError:", e)  # Log the exact error in the terminal
            return JsonResponse({'error': 'Invalid field name in query'}, status=400)
        except Exception as e:
            print("Unexpected Error:", e)  # Log other potential errors
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    return JsonResponse({'students': []})


def get_club_members(request, club_id):
    """Fetch updated list of club members"""
    club = get_object_or_404(Club, id=club_id)
    members = club.members.all()  # Fetch members

    # Format data for frontend
    members_data = [
        {
            "id": member.id,
            "admission_no": member.admission_number,
            "name": f"{member.first_name} {member.last_name}",
            "grade": member.grade,
            "role": "Member"  # Adjust this based on your logic
        }
        for member in members
    ]

    return JsonResponse({"members": members_data})


@csrf_exempt  # Remove this in production, use proper CSRF protection
def remove_member(request, club_id, student_id):
    if request.method == 'POST':
        club = get_object_or_404(Club, id=club_id)
        student = get_object_or_404(Student, id=student_id)

        club.members.remove(student)  # Remove student from the club
        return JsonResponse({'status': 'success', 'message': 'Member removed successfully'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def mark_club_attendance(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    if request.method == "POST":
        present_students = request.POST.getlist("attendance")
        for student in club.members.all():
            student.is_present = str(student.id) in present_students
            student.save()
    return render(request, 'schedules/attendance_mark.html', {'club': club})

# def create_event(request, club_id):
#     club = get_object_or_404(Club, id=club_id)
#     if request.method == "POST":
#         name = request.POST['name']
#         date = request.POST['date']
#         description = request.POST['description']
#         ClubEvent.objects.create(name=name, date=date, description=description, club=club)
#         return redirect('club_detail', club_id=club.id)
#     return render(request, 'schedules/event_create.html', {'club': club})
