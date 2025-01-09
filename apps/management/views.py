import json
import logging
from datetime import date, timedelta, datetime

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions.datetime import TruncMonth, ExtractYear
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django_daraja.mpesa.core import MpesaClient

from apps.accounts.models import FeePayment, Expense
from apps.management.forms import SubjectForm, BookForm
from apps.management.models import Term, Subject, Result, Teacher, TeacherSubject, ReportCard, SubjectMark, ExamType
from apps.students.forms import SendSMSForm, SendClassForm
from apps.students.models import Book, Transaction, Student, Payment, Class, Parent, StudentParent

# Create your views here.
from django.db.models import Avg, Sum, Count, Q

from apps.students.utils import MobileSasaAPI
from apps.teachers.models import Department  # Revenue

logger = logging.getLogger(__name__)


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
    grades = Class.objects.all()  # Fetch all grades for the dropdown

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


# @csrf_exempt
# def send_sms(request):
#     if request.method == "POST":
#         # Get phone number and message from the request
#         phone = request.POST.get("phone")
#         message = request.POST.get("message")
#
#         # Prepare the payload for the API request
#         api_token = MobileSasaAPI() # Replace with your API token
#         url = "https://api.mobilesasa.com/v1/send/message"
#         headers = {
#             "Authorization": f"Bearer {api_token}",
#             "Accept": "application/json",
#             "Content-Type": "application/json"
#         }
#
#         data = {
#             "senderID": "MOBILESASA",  # Replace with your sender ID
#             "message": message,
#             "phone": phone
#         }
#
#         try:
#             response = requests.post(url, json=data, headers=headers)
#
#             # Log or print the response content for debugging
#             print(response.text)  # Logs the response body
#
#             if response.status_code == 200:
#                 response_data = response.json()
#                 if response_data["status"]:
#                     return JsonResponse({
#                         "status": "success",
#                         "message": "SMS sent successfully",
#                         "messageId": response_data.get("messageId")
#                     })
#                 else:
#                     return JsonResponse({
#                         "status": "error",
#                         "message": response_data.get("message")
#                     })
#             else:
#                 return JsonResponse({
#                     "status": "error",
#                     "message": "Failed to send SMS. Try again later."
#                 })
#
#         except requests.exceptions.RequestException as e:
#             return JsonResponse({
#                 "status": "error",
#                 "message": f"An error occurred: {str(e)}"
#             })
#
#
#     else:
#         return JsonResponse({
#             "status": "error",
#             "message": "Invalid request method"
#         })


@login_required
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subjects_list')  # Redirect to a list of all subjects
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

    return render(request, "Home/index.html", {
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
    teacher_subjects = TeacherSubject.objects.select_related('teacher', 'subject',
                                                             'grade_assigned').all()  # or use any other filter you need
    return render(request, 'performance/subject_teachers.html', {'teacher_subjects': teacher_subjects})


@login_required
def subjects_by_grade(request, grade_id):
    grade = Class.objects.get(id=grade_id)
    subjects = TeacherSubject.objects.filter(grade_assigned=grade).select_related('teacher', 'subject',
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
    exam_type_id = request.GET.get('exam_type_id')  # Added exam_type_id parameter

    # Redirect to the results table if all parameters are provided
    if grade_id and term_id and subject_id and exam_type_id:
        return redirect(
            reverse('add_results_table') +
            f'?grade_id={grade_id}&term_id={term_id}&subject_id={subject_id}&exam_type_id={exam_type_id}'
        )

    # Populate filter form options
    grades = Class.objects.all()  # Assuming Class model represents grades
    terms = Term.objects.all()
    subjects = Subject.objects.all()
    exam_types = ExamType.objects.all()  # Added exam types

    return render(request, 'performance/filter_form.html', {
        'classes': grades,
        'terms': terms,
        'subjects': subjects,
        'exam_types': exam_types,  # Pass exam types to the template
    })


# Add or Update Results Table View


def add_results_table(request):
    class_id = request.GET.get('grade_id')
    term_id = request.GET.get('term_id')
    subject_id = request.GET.get('subject_id')
    exam_type_id = request.GET.get('exam_type_id')  # Added exam_type_id parameter

    if not (class_id and term_id and subject_id and exam_type_id):
        return redirect('filter_results')

    selected_class = get_object_or_404(Class, id=class_id)
    selected_term = get_object_or_404(Term, id=term_id)
    selected_subject = get_object_or_404(Subject, id=subject_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    # Fetch students in the selected class
    students = Student.objects.filter(grade=selected_class)

    # Prepare initial data to populate marks if they exist
    initial_data = []
    for student in students:
        subject_mark = SubjectMark.objects.filter(
            student=student,
            subject=selected_subject,
            term=selected_term,
            exam_type=selected_exam_type
        ).first()
        initial_data.append({
            'student': student,
            'marks': subject_mark.marks if subject_mark else "",
        })

    if request.method == 'POST':
        for student in students:
            marks = request.POST.get(f'marks_{student.id}')  # Get marks input for each student
            if marks:
                # Update or create the SubjectMark
                subject_mark, created = SubjectMark.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    term=selected_term,
                    exam_type=selected_exam_type,
                    defaults={'marks': marks}
                )
        messages.success(request, "Marks have been successfully updated!")
        return redirect('view_results_table', grade_id=class_id, term_id=term_id, subject_id=subject_id,
                        exam_type_id=exam_type_id)

    context = {
        'selected_class': selected_class,
        'selected_term': selected_term,
        'selected_subject': selected_subject,
        'selected_exam_type': selected_exam_type,
        'students': students,
        'initial_data': initial_data,
    }
    return render(request, 'performance/add_results_table.html', context)


# View Results Table


# def view_results_table(request, grade_id, term_id, exam_type_id):
#     # Get selected class, term, and exam type
#     selected_class = get_object_or_404(Class, id=grade_id)
#     selected_term = get_object_or_404(Term, id=term_id)
#     selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)
#
#     # Fetch all subjects for the selected class
#     subjects = Subject.objects.filter(grade=selected_class)
#
#     # Fetch all students in the selected class
#     students = Student.objects.filter(grade=selected_class)
#
#     # Prepare marks data for each student
#     student_data = []
#     for student in students:
#         marks = []
#         for subject in subjects:
#             subject_mark = SubjectMark.objects.filter(
#                 student=student,
#                 subject=subject,
#                 term=selected_term,
#                 exam_type=selected_exam_type
#             ).first()
#             marks.append(subject_mark.marks if subject_mark else "-")
#         student_data.append({
#             'admission_number': student.admission_number,
#             'name': f"{student.first_name} {student.last_name}",
#             'marks': marks,
#         })
#
#     context = {
#         'selected_class': selected_class,
#         'selected_term': selected_term,
#         'selected_exam_type': selected_exam_type,
#         'subjects': subjects,
#         'student_data': student_data,
#     }
#     return render(request, 'performance/view_results_table.html', context)

def view_results_table(request, grade_id, term_id, exam_type_id, subject_id):
    # Get selected class, term, exam type, and subject
    selected_class = get_object_or_404(Class, id=grade_id)
    selected_term = get_object_or_404(Term, id=term_id)
    selected_exam_type = get_object_or_404(ExamType, id=exam_type_id)

    # Fetch all subjects for the selected class (all subjects, not just the selected subject)
    subjects = Subject.objects.filter(grade=selected_class)

    # Fetch students in the selected class
    students = Student.objects.filter(grade=selected_class)

    # Prepare marks data for each student
    student_data = []
    for student in students:
        marks = []
        for subject in subjects:
            # Get SubjectMark for each subject
            subject_mark = SubjectMark.objects.filter(
                student=student,
                subject=subject,
                term=selected_term,
                exam_type=selected_exam_type
            ).first()

            # Append the marks or "-" if no marks found
            marks.append(subject_mark.marks if subject_mark else "-")

        student_data.append({
            'admission_number': student.admission_number,
            'name': f"{student.first_name} {student.last_name}",
            'marks': marks,
        })

    # Context to pass to the template
    context = {
        'selected_class': selected_class,
        'selected_term': selected_term,
        'selected_exam_type': selected_exam_type,
        'subjects': subjects,
        'student_data': student_data,
    }

    return render(request, 'performance/view_results_table.html', context)


def report_card_view(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    report_card, created = ReportCard.objects.get_or_create(student=student, term=term)

    total_marks = report_card.total_marks()  # Calculate total marks
    return render(request, 'report_card.html', {
        'student': student,
        'term': term,
        'total_marks': total_marks,
    })


#
# def add_results(request):
#     if request.method == "POST":
#         form = AddResultForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Result added successfully!")
#             return redirect('add_results')
#     else:
#         form = AddResultForm()
#
#     return render(request, "performance/add_results.html", {"form": form})
#
#
# def add_results_by_class(request):
#     class_id = request.GET.get('class_id')  # Class filter
#     term_id = request.GET.get('term_id')  # Term filter
#     show_table = request.GET.get('show_table', False)  # Determine if table view is needed
#     subject_id = request.GET.get('subject_id')  # Subject filter
#
#     if class_id and term_id:
#         class_obj = Class.objects.get(id=class_id)
#         term = Term.objects.get(id=term_id)
#         students = Student.objects.filter(grade=class_obj)
#         subjects = Subject.objects.all()  # Fetch all subjects for the grade
#
#         # Prepare existing marks
#         marks = SubjectMark.objects.filter(term=term, student__in=students)
#         marks_dict = {}
#         for mark in marks:
#             if mark.student.id not in marks_dict:
#                 marks_dict[mark.student.id] = {}
#             marks_dict[mark.student.id][mark.subject.id] = mark.marks
#
#         if request.method == "POST":
#             subject = Subject.objects.get(id=subject_id)
#             for student in students:
#                 mark_value = request.POST.get(f'marks_{student.id}')
#                 if mark_value:
#                     SubjectMark.objects.update_or_create(
#                         student=student,
#                         subject=subject,
#                         term=term,
#                         defaults={"marks": int(mark_value)},
#                     )
#             # Redirect to the same table view
#             return redirect(f'/management/results/?class_id={class_id}&term_id={term_id}&show_table=True')
#
#         if show_table:
#             return render(request, 'performance/students_results_table.html', {
#                 'class_obj': class_obj,
#                 'term': term,
#                 'subjects': subjects,
#                 'students': students,
#                 'marks_dict': marks_dict,
#             })
#
#     classes = Class.objects.all()
#     terms = Term.objects.all()
#     subjects = Subject.objects.all()
#     return render(request, 'performance/filter_form.html', {'classes': classes, 'terms': terms, 'subjects': subjects})
#
# def student_results_table(request, student_id, term_id):
#     # Fetch student and term
#     student = Student.objects.get(id=student_id)
#     term = Term.objects.get(id=term_id)
#
#     # Get all subjects
#     subjects = Subject.objects.all()
#
#     # Fetch subject marks for the student in the term
#     subject_marks = SubjectMark.objects.filter(student=student, term=term)
#
#     # Map marks to subjects
#     marks_by_subject = {mark.subject.name: mark.marks for mark in subject_marks}
#
#     context = {
#         "student": student,
#         "term": term,
#         "subjects": subjects,
#         "marks_by_subject": marks_by_subject,
#     }
#     return render(request, "performance/student_performance.html", context)
#

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

    return render(request, "Home/index.html", {"total_revenue": total_revenue})


# def line_chart(request):
#     transactions = Transaction.objects.filter(created_at__year=2024)
#     grouped  = transactions.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
#     numbers = []
#     months = []
#     for i in grouped:
#         numbers.append(i['count'])
#         months.append(i['month'].strftime("%b"))
#     return JsonResponse({
#         "title": "Transactions Grouped By Month",
#         "data": {
#             "labels": months,
#             "datasets": [{
#                 "label": "Count",
#                 "lineTension": 0.3,
#                 "backgroundColor": "rgba(78, 115, 223, 0.05)",
#                 "borderColor": "rgba(78, 115, 223, 1)",
#                 "pointRadius": 3,
#                 "pointBackgroundColor": "rgba(78, 115, 223, 1)",
#                 "pointBorderColor": "rgba(78, 115, 223, 1)",
#                 "pointHoverRadius": 3,
#                 "pointHoverBackgroundColor": "rgba(78, 115, 223, 1)",
#                 "pointHoverBorderColor": "rgba(78, 115, 223, 1)",
#                 "pointHitRadius": 10,
#                 "pointBorderWidth": 2,
#                 "data": numbers,
#             }],
#         },

#     })


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


# @login_required
# def gender_pie_data(request):
#     current_year = datetime.now().year
#
#     boys_count = Student.objects.filter(gender="Male", joining_date__year=current_year).count()
#     girls_count = Student.objects.filter(gender="Female", joining_date__year=current_year).count()
#
#     return JsonResponse({
#         "title": "Gender Ratio for the Year",
#         "labels": ["Boys", "Girls"],
#         "datasets": [{
#             "data": [boys_count, girls_count],
#             "backgroundColor": ["#0a3622", "#008374"],  # Deep green and teal for initial display
#             "hoverBackgroundColor": ["#106b45", "#00a38d"],  # Brighter shades on hover
#             "hoverBorderColor": "rgba(234, 236, 244, 1)",  # Light border on hover
#         }]
#     })


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


# def gender_data(request):
#     current_year = datetime.now().year
#
#     # Yearly trend data
#     boys_data = (
#         Student.objects.filter(gender="Male")
#         .annotate(year=ExtractYear("joining_date"))
#         .values("year")
#         .annotate(count=Count("id"))
#         .order_by("year")
#     )
#
#     girls_data = (
#         Student.objects.filter(gender="Female")
#         .annotate(year=ExtractYear("joining_date"))
#         .values("year")
#         .annotate(count=Count("id"))
#         .order_by("year")
#     )
#
#     years = sorted(set([item["year"] for item in boys_data] + [item["year"] for item in girls_data]))
#     boys_counts = [next((item["count"] for item in boys_data if item["year"] == year), 0) for year in years]
#     girls_counts = [next((item["count"] for item in girls_data if item["year"] == year), 0) for year in years]
#
#     # Current year pie chart data
#     boys_count = Student.objects.filter(gender="Male", joining_date__year=current_year).count()
#     girls_count = Student.objects.filter(gender="Female", joining_date__year=current_year).count()
#
#     return JsonResponse({
#         "yearly_trend": {
#             "years": years,
#             "boys": boys_counts,
#             "girls": girls_counts,
#         },
#         "current_year_pie": {
#             "title": f"Gender Ratio for {current_year}",
#             "labels": ["Boys", "Girls"],
#             "datasets": [{
#                 "data": [boys_count, girls_count],
#                 "backgroundColor": ["#4e73df", "#ff6384"],
#                 "hoverBackgroundColor": ["#2e59d9", "#e57373"],
#                 "hoverBorderColor": "rgba(234, 236, 244, 1)",
#             }]
#         }
#     })


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


#
# def filter_results(request):
#     classes = Class.objects.all()  # Replace with your class model
#     terms = Term.objects.all()
#     subjects = Subject.objects.all()
#
#     students = None
#     if request.GET:
#         class_id = request.GET.get('class')
#         term_id = request.GET.get('term')
#         test = request.GET.get('test')
#         subject_id = request.GET.get('subject')
#
#         # Filter students based on class
#         students = Student.objects.filter(Class_id=class_id)
#
#     return render(request, 'performance/query_students.html', {
#         'classes': classes,
#         'terms': terms,
#         'subjects': subjects,
#         'students': students,
#     })
#
# def save_results(request,student_id):
#     if request.method == "POST":
#         student = get_object_or_404(Student, id=student_id)
#         term = Term.objects.get(id=request.POST['term_id'])
#         subject = Subject.objects.get(id=request.POST['subject_id'])
#         test = request.POST['test']
#         score = request.POST['score']
#
#         # Save the result
#         Result.objects.create(
#             student=student,
#             term=term,
#             subject=subject,
#             test_type=test,
#             score=score,
#         )
#     return redirect('view_results')


def exam_list(request):
    return render(request, 'performance/exam_list.html')


def time_table(request):
    return render(request, 'performance/time_table.html')


def transport_view(request):
    return render(request, 'performance/transport.html')


def events_view(request):
    return render(request, 'Manage/event.html')
