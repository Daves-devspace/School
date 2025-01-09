from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from collections import defaultdict
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.transaction import atomic
from django.http import JsonResponse, Http404

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from apps.accounts.models import FeeStructure, FeeRecord
from apps.management.models import Term, SubjectMark, ReportCard, ExamType, Subject
from apps.students.forms import StudentForm, PromoteStudentsForm, SendSMSForm
# from apps.students.forms import StudentForm
from apps.students.models import Student, Parent, StudentParent, Grade


logger = logging.getLogger(__name__)


# Create your views here.
@login_required
def students(request):
    student_list = Student.objects.filter(status="Active")
    return render(request, "students/students.html", {"student_list": student_list})


def active_students(request):
    # students_active = Student.objects.filter(status="active")
    students_active = Student.objects.filter(status="Active")
    return render(request, "students/All-students.html", {"students_active": students_active})


def update_student_status(request):
    if request.method == 'POST':
        # get list of selected student
        selected_students = request.POST.getlist("selected_students")  # grabs list of selected student

        if not selected_students:
            messages.error(request, "No students selected.")
            return redirect('active_students')
        try:
            # update status of selected to graduate
            with transaction.atomic():
                students = Student.objects.filter(id__in=selected_students, status="Active")
                students.update(status="graduated")
            messages.success(request, f"Successfully updated {students.count()} student(s) to 'Graduated'. ")
            return redirect("active_students")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect("active_students")
    else:
        # handle get request(students)
        students_active = Student.objects.filter(status="active")
        return render(request, "students/All-students.html", {"students_active": students_active})


def reverse_student_status(request):
    if request.method == "POST":
        # Get the list of selected student IDs
        selected_students = request.POST.getlist("selected_students")

        if not selected_students:
            messages.error(request, "No students selected")
            return redirect("active_students")
        try:
            # revert the status of selected students to active
            with transaction.atomic():
                students = Student.objects.filter(id__in=selected_students, status="graduated")
                students.update(status="Active")
            messages.success(request, f"Successfully reverted {students.count()} students to 'Active")
            return redirect("active_students")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect("active_students")
    else:
        # if get method show graduated students
        students_graduated = Student.objects.filter(status="graduated")
        return render(request, 'students/students_graduated.html', {"students_graduated": students_graduated})


# promote students to next class and the completed students marked as graduated
def promote_students():
    from django.db.models import Max
    from django.utils.timezone import now
    # fetching the max grade -grade 9/form 4
    max_level = Grade.objects.aggregate(max_level=Max('level'))['max_level']

    if max_level is None:
        return {"students_promoted": 0, "students_graduated": 0}  # No classes available

    students_promoted_count = 0

    # promote students
    with transaction.atomic():
        current_year = datetime.now().year
        students_to_promote = Student.objects.filter(status='active', Class__level__lt=max_level,
                                                     ).exclude(
            last_promoted__year=current_year)  # Exclude students already promoted this year

        for student in students_to_promote:
            next_class = Grade.objects.filter(level=student.grade.level + 1).first()
            if next_class:
                student.grade = next_class
                student.last_promoted = now()
                student.save()
                students_promoted_count += 1

    # mark students as graduated
    students_to_graduate = Student.objects.filter(status="active", Class__level=max_level)
    students_to_graduate.update(status="graduated")

    return {
        "students_promoted": students_promoted_count,
        "students_graduated": students_to_graduate.count()
    }


def promote_students_view(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                students = Student.objects.filter(status="Active")  # All active students
                promoted_count = 0
                graduated_count = 0
                errors = []
                current_year = now().year

                for student in students:
                    try:
                        # Check if the student has been promoted in the current year
                        if student.last_promoted and student.last_promoted.year == current_year:
                            # Skip promotion if already promoted in the current year
                            errors.append(f"{student}: Already promoted this year.")
                            continue

                        result = student.promote()
                        if result == "Promoted":
                            promoted_count += 1
                        elif result == "Graduated":
                            graduated_count += 1
                        elif result.startswith("Error"):
                            errors.append(f"{student}: {result}")
                    except Exception as e:
                        errors.append(f"{student}: {str(e)}")

                # Success message with the number of students promoted and graduated
                messages.success(
                    request,
                    f"{promoted_count} students promoted and {graduated_count} students graduated successfully."
                )

                # If errors occurred, show a warning message
                if errors:
                    messages.warning(request, f"Errors occurred for {len(errors)} students: {', '.join(errors)}")

        except Exception as e:
            messages.error(request, f"An error occurred during promotion: {str(e)}")

        return redirect("students")  # Redirect to the student list page
    else:
        return render(request, "students/confirm_promotion.html")


# # current term
# def get_current_term():
#     # Get today's date
#     today = date.today()
#
#     try:
#         # Fetch the current term from the database based on today's date
#         current_term = Term.objects.get(start_date__lte=today, end_date__gte=today)
#         return current_term
#     except Term.DoesNotExist:
#         raise Exception(
#             "No active term found for today's date. Please ensure terms are correctly set up in the database.")
#
def get_next_term():
    """
    Get the next upcoming term based on today's date.
    """
    today = date.today()
    try:
        # Fetch the next term (closest to today and starting in the future)
        upcoming_terms = Term.objects.filter(start_date__gt=today).order_by("start_date")
        return upcoming_terms.first()
    except Term.DoesNotExist:
        return None


def get_current_term():
    """
    Get the current active term based on today's date.
    """
    today = date.today()
    try:
        # Fetch the current term from the database
        current_term = Term.objects.get(start_date__lte=today, end_date__gte=today)
        return current_term
    except Term.DoesNotExist:
        return None


def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()  # Save the student instance
            try:
                # Fetch the current term
                current_term = get_current_term()

                # If no current term, fetch the next term (holiday period)
                if not current_term:
                    current_term = get_next_term()

                if current_term:
                    # Get the Grade from the GradeSection assigned to the student
                    grade_section = student.grade  # This is the GradeSection instance
                    grade = grade_section.grade  # This is the Grade (e.g., Grade 1)

                    if grade:
                        # Fetch the fee structure based on the Grade
                        fee_structure = FeeStructure.objects.filter(
                            grade=grade,
                            term=current_term
                        ).first()

                        if fee_structure:
                            # Create the fee record for the student
                            FeeRecord.objects.create(
                                student=student,
                                term=current_term,
                                tuition_fee=fee_structure.tuition_fee,
                                paid_amount=0,
                                due_date=current_term.end_date
                            )
                            messages.success(
                                request,
                                f"Fee record created for {student.first_name} {student.last_name} in {current_term.name} with total fee {fee_structure.tuition_fee}."
                            )
                        else:
                            messages.warning(
                                request,
                                f"No fee structure found for grade {grade.name} in term {current_term.name}. Please set up the fee structure."
                            )
                    else:
                        messages.warning(
                            request,
                            "The student is not assigned to a valid grade. Please check the grade assignment."
                        )
                else:
                    messages.error(
                        request,
                        "No active or upcoming term found. Please ensure terms are set up in the system."
                    )
            except Exception as e:
                messages.error(request, f"An error occurred while assigning fees: {str(e)}")

            return redirect("students")  # Redirect to the desired page
    else:
        form = StudentForm()

    return render(request, "students/add-student.html", {"form": form})

# def student_details(request, id):
#     student = Student.objects.get(pk=id)
#     report_cards = ReportCard.objects.filter(student=student)  # Fetch all report cards for the student
#     subject_marks = SubjectMark.objects.filter(student=student)  # Fetch subject marks for all terms
#
#     # Optionally, fetch the current or latest term's report card
#     latest_term = get_current_term()
#     latest_report_card = None
#     if latest_term:
#         latest_report_card = report_cards.filter(term=latest_term).first()
#
#
#
#     context = {
#         'student': student,
#         'report_cards': report_cards,
#         'subject_marks': subject_marks,
#         'latest_report_card': latest_report_card,
#     }
#     return render(request, 'students/student-details.html', context)




def get_student_performance_data(student, selected_term=None, selected_year=None):
    """
    Fetch and structure student performance data for use in a chart,
    optionally filtering by a specific term and year.
    Defaults to the current term if no term is selected.
    """
    if not hasattr(student, 'grade') or not hasattr(student.grade, 'grade'):
        raise ValueError(f"Student {student.id} is not linked to a Grade instance.")

    grade_instance = student.grade.grade

    # Default to current term if no term is selected
    terms = [selected_term] if selected_term else [get_current_term()]

    if not terms:
        raise ValueError("[ERROR] No valid terms found for processing.")

    # Filter terms by year if a specific year is provided
    if selected_year:
        try:
            selected_year = int(selected_year)
            terms = [term for term in terms if term.start_date.year == selected_year]
        except ValueError:
            raise ValueError('Invalid year parameter.')

        if not terms:
            print(f"[DEBUG] No terms found for the year {selected_year}.")  # Debug log

    # Fetch the exam types based on the selected terms
    exam_types = ExamType.objects.filter(term__in=terms)
    subjects = Subject.objects.filter(grade=grade_instance)
    labels = list(subjects.values_list('name', flat=True))

    if not labels:
        print(f"[DEBUG] No subjects found for grade {grade_instance.id}.")  # Debug log
        return {
            'student_name': student.first_name,
            'labels': [],
            'datasets': [],
        }

    # Initialize marks data structure for storing marks per term, exam, and subject
    marks_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)))  # Initialize with None for missing data

    # Populate marks_data with default values for each subject in the selected terms and exams
    for term in terms:
        exams = exam_types.filter(term=term)
        for exam in exams:
            for subject_name in labels:
                marks_data[term.name][exam.name.lower()][subject_name] = 0

    # Retrieve report cards for the student in the selected terms
    report_cards = ReportCard.objects.filter(student=student, term__in=terms).select_related('term', 'exam_type')
    subject_marks = SubjectMark.objects.filter(report_card__in=report_cards).select_related('subject', 'report_card__term', 'report_card__exam_type')

    if not report_cards.exists():
        print(f"[DEBUG] No report cards found for student {student.id} in terms: {[term.name for term in terms]}.")
    if not subject_marks.exists():
        print(f"[DEBUG] No subject marks found for student {student.id}.")

    # Populate marks_data with actual marks for each subject in the report cards
    for subject_mark in subject_marks:
        term_name = subject_mark.report_card.term.name
        exam_name = subject_mark.report_card.exam_type.name.lower()
        subject_name = subject_mark.subject.name
        marks_data[term_name][exam_name][subject_name] = subject_mark.marks if subject_mark.marks is not None else 0

    # Prepare the datasets for the chart
    datasets = []
    for exam_type in exam_types:
        dataset = {'name': exam_type.name, 'data': []}
        for term in terms:
            term_data = marks_data[term.name][exam_type.name.lower()]
            dataset['data'].extend([term_data.get(subject_name, 0) for subject_name in labels])
        datasets.append(dataset)

    # Return the structured chart data
    chart_data = {
        'student_name': student.first_name,
        'labels': labels,
        'datasets': datasets,
    }
    return chart_data



def get_student_chart_data(request, student_id, term, year):
    try:
        # Fetch student by ID
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        # Return error if student doesn't exist
        return JsonResponse({"error": f"Student with ID {student_id} does not exist."}, status=404)

    try:
        # Find term for the specific year
        selected_term = Term.objects.filter(name=term, start_date__year=year).first()
        if not selected_term:
            get_current_term()
            return JsonResponse({"error": f"No term found for {term} in {year}."}, status=404)
    except Term.DoesNotExist:
        # Return error if term doesn't exist
        return JsonResponse({"error": f"Term {term} not found for year {year}."}, status=404)

    try:
        # Get performance data for the student and selected term
        chart_data = get_student_performance_data(student, selected_term=selected_term)
        if not chart_data:
            return JsonResponse({"error": "No performance data available for the selected term."}, status=404)

        # Return chart data as a JSON response
        return JsonResponse(chart_data, safe=False)

    except Exception as e:
        # Handle unexpected errors
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)






def student_details(request, id):
    # Fetch student details
    student = get_object_or_404(Student, pk=id)

    # Fetch report cards and subject marks for the student
    report_cards = ReportCard.objects.filter(student=student).select_related('term').only('term', 'exam_type', 'student')
    subject_marks = SubjectMark.objects.filter(report_card__student=student).select_related('subject', 'exam_type').only('marks', 'subject', 'report_card')

    student_parents = StudentParent.objects.filter(student=student)
    chart_data = get_student_performance_data(student)

    # Fetch all terms and distinct years
    terms = Term.objects.all()
    years = Term.objects.values_list('start_date__year', flat=True).distinct().order_by('start_date__year')


    # Fetch the current or latest term's report card
    latest_term = get_current_term()
    latest_report_card = None
    if latest_term:
        latest_report_card = report_cards.filter(term=latest_term).first()

    # Prepare detailed report card information
    report_card_details = [
        {
            'report_card': rc,
            'total_marks': rc.calculate_total_marks() if hasattr(rc, 'total_marks') else 0,  # Safe handling
            'rank': rc.student_rank() if hasattr(rc, 'student_rank') else None,
        }
        for rc in report_cards
    ]

    # Context for rendering the template
    context = {
        'student': student,
        'report_cards': report_card_details,
        'subject_marks': subject_marks,
        'latest_report_card': latest_report_card,
        'latest_term': latest_term,
        'student_parents': student_parents,
        'chart_data': chart_data,
        'terms': terms,  # Pass terms to populate dropdown
        'years': years,  # Pass years to populate dropdown
    }
    return render(request, 'students/student-details.html', context)



# def student_details(request, id):
#     student = get_object_or_404(Student, pk=id)
#     report_cards = ReportCard.objects.filter(student=student)  # Fetch all report cards for the student
#     subject_marks = SubjectMark.objects.filter(student=student)  # Fetch subject marks for all terms
#
#     # Optionally, fetch the current or latest term's report card
#     latest_term = get_current_term()
#     latest_report_card = None
#     if latest_term:
#         latest_report_card = report_cards.filter(term=latest_term).first()
#
#     # For each report card, calculate the total marks (if you have a method for that)
#     report_card_details = []
#     for report_card in report_cards:
#         total_marks = report_card.total_marks()  # Assuming this method is defined in your model
#         print(f"Report Card for Term: {report_card.term.name}, Total Marks: {total_marks}")
#         report_card_details.append({
#             'report_card': report_card,
#             'total_marks': total_marks
#         })
#
#     context = {
#         'student': student,
#         'report_cards': report_card_details,
#         'subject_marks': subject_marks,
#         'latest_report_card': latest_report_card,
#     }
#     return render(request, 'students/student-details.html', context)


@login_required
def edit_student(request, id):
    student = get_object_or_404(Student, pk=id)
    parents = Parent.objects.all()

    # Get the first StudentParent relationship for this student
    student_parent_rel = StudentParent.objects.filter(student=student).first()

    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            try:
                with transaction.atomic():  # Ensure atomicity for all database updates
                    student = form.save()

                    # Handle parent details update
                    if student_parent_rel:
                        # Check if a parent with the updated details already exists
                        parent_first_name = request.POST.get("parent_first_name", "").strip()
                        parent_last_name = request.POST.get("parent_last_name", "").strip()
                        parent_mobile = request.POST.get("parent_mobile", "").strip()

                        existing_parent = Parent.objects.filter(
                            first_name=parent_first_name,
                            last_name=parent_last_name,
                            mobile=parent_mobile
                        ).exclude(id=student_parent_rel.parent.id).first()

                        if existing_parent:
                            # Associate the student with the existing parent
                            student_parent_rel.parent = existing_parent
                        else:
                            # Update the current parent if no duplicate exists
                            parent = student_parent_rel.parent
                            parent.first_name = parent_first_name
                            parent.last_name = parent_last_name
                            parent.mobile = parent_mobile
                            parent.email = request.POST.get("parent_email", parent.email)
                            parent.address = request.POST.get("parent_address", parent.address)
                            parent.save()

                        # Update relationship field (if provided)
                        relationship = request.POST.get("parent_relationship", student_parent_rel.relationship)
                        student_parent_rel.relationship = relationship
                        student_parent_rel.save()

                    # Handle parent reassignments if a new parent is selected
                    if 'parents' in request.POST:
                        parent_ids = request.POST.getlist('parents')
                        parent_objects = Parent.objects.filter(id__in=parent_ids)

                        # Reassign parents without duplicating
                        student.parent.set(parent_objects)

                    messages.success(request, f"Student {student.first_name} {student.last_name} updated successfully!")
                    return redirect("students")
            except Exception as e:
                messages.error(request, f"Error updating student: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize form with student instance and parent data
        initial_data = {}
        if student_parent_rel:
            parent = student_parent_rel.parent
            initial_data.update({
                'parent_first_name': parent.first_name,
                'parent_last_name': parent.last_name,
                'parent_mobile': parent.mobile,
                'parent_email': parent.email,
                'parent_address': parent.address,
                'parent_relationship': student_parent_rel.relationship,
            })

        form = StudentForm(instance=student, initial=initial_data)

    context = {
        'form': form,
        'student': student,
        'parents': parents,
        'selected_parents': list(student.parent.values_list('id', flat=True)),
    }

    return render(request, "students/edit-student.html", context)


@login_required
def delete_student(request, id):
    student = Student.objects.get(pk=id)
    student.delete()
    messages.info(request, f"Student {student.first_name} was deleted")
    return redirect('students')


def students_grid(request):
    student_grid = Student.objects.all()
    return render(request, 'students/students_grid.html', {'student_grid': student_grid})
