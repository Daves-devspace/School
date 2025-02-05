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
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.models import FeeStructure, FeeRecord
from apps.management.models import Term, SubjectMark, ReportCard, ExamType, Attendance
from apps.students.forms import StudentForm, PromoteStudentsForm, SendSMSForm, DocumentUploadForm,  \
    StudentSearchForm
# from apps.students.forms import StudentForm
from apps.students.models import Student, Parent, StudentParent, Grade, GradeSection, StudentDocument

logger = logging.getLogger(__name__)


# Create your views here.
@login_required
def students(request):
    student_list = Student.objects.filter(status="Active")
    return render(request, "students/students.html", {"student_list": student_list})



def student_query(request):
    form = StudentSearchForm(request.GET)
    students = Student.objects.all()  # Start with all students

    if form.is_valid():
        grade_name = form.cleaned_data.get('grade')  # User enters grade name
        section_name = form.cleaned_data.get('section')  # User enters section name

        if grade_name:
            students = students.filter(grade__grade__name__icontains=grade_name)  # Correct field reference
        if section_name:
            students = students.filter(grade__section__name__icontains=section_name)

    context = {
        'students': students,
        'form': form,
        'student_count': students.count()
    }
    return render(request, 'students/query_students.html', context)





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
        selected_students = request.POST.getlist("selected_students")

        if not selected_students:
            messages.error(request, "No students selected")
            return redirect("reverse_student_status")

        try:
            with transaction.atomic():
                students = Student.objects.filter(id__in=selected_students, status="Graduated")
                count = students.count()
                students.update(status="Active")

            messages.success(request, f"Successfully reverted {count} students to 'Active'")
            return redirect("reverse_student_status")

        except Exception as e:
            logger.error(f"Error reverting student status: {e}")
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect("reverse_student_status")

    students_graduated = Student.objects.filter(status="Graduated")
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
                            errors.append(f"{student}:  Already promoted this year.")
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

@csrf_exempt
def get_student_performance_data(request, term_id, year, student_id):
    try:
        term = Term.objects.get(id=term_id, start_date__year=year)


        # Fetch subject marks for the student in the selected term
        subject_marks = SubjectMark.objects.filter(
            student_id=student_id,
            term=term
        ).select_related('exam_type', 'subject')

        if not subject_marks.exists():
            return {"labels": [], "datasets": []}  # Return empty data

        # Ensure unique subjects for labels
        subjects = subject_marks.values_list('subject__name', flat=True).distinct()
        chart_data = {
            "labels": list(subjects),  # Unique subjects list
            "datasets": []
        }

        # Group data by exam_type
        exam_types = subject_marks.values_list('exam_type__name', flat=True).distinct()
        for exam_type in exam_types:
            dataset = {
                "name": exam_type,
                "data": [mark.marks for mark in subject_marks.filter(exam_type__name=exam_type)]
            }
            chart_data["datasets"].append(dataset)

        return chart_data  # Return structured data


    except Term.DoesNotExist:

        return JsonResponse({"error": f"No term found for {term_id} in {year}."}, status=404)


@csrf_exempt
def get_student_chart_data(request, student_id, term, year):
    try:
        # Fetch student by ID
        student = get_object_or_404(Student, id=student_id)

        # Find term for the specific year
        selected_term = Term.objects.filter(name=term, start_date__year=year).first()
        if not selected_term:
            return JsonResponse({"error": f"No term found for {term} in {year}."}, status=404)

        # Get performance data
        chart_data = get_student_performance_data(
            request, term_id=selected_term.id, year=year, student_id=student.id
        )

        # Return JSON response
        return JsonResponse(chart_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)



def student_details(request, id):
    # Fetch student details
    student = get_object_or_404(Student, pk=id)

    # Handle status change request (Activate/Deactivate student)
    if request.method == 'POST' and 'toggle_status' in request.POST:
        try:
            with transaction.atomic():
                if student.status == "Graduated":
                    student.status = "Active"
                    messages.success(request, f"{student.first_name} has been reactivated.")
                else:
                    student.status = "Graduated"
                    messages.success(request, f"{student.first_name} has been deactivated (Graduated).")
                student.save()
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        return redirect('student_details', id=student.id)

    # Handle document uploads
    if request.method == 'POST' and 'upload_document' in request.POST:
        document_form = DocumentUploadForm(request.POST, request.FILES)
        if document_form.is_valid():
            document = document_form.save(commit=False)  # Don't save yet
            document.student = student  # Associate with student
            document.save()  # Now save
            messages.success(request, "Document uploaded successfully!")
            return redirect('student_details', id=student.id)
        else:
            messages.error(request, "Failed to upload document. Please try again.")

    else:
        document_form = DocumentUploadForm()

    # Fetch all terms and distinct years
    terms = Term.objects.all()
    years = Term.objects.values_list('start_date__year', flat=True).distinct().order_by('start_date__year')

    # Get selected term and year from the request
    selected_term_id = request.GET.get('term_id')
    selected_year = request.GET.get('year')

    # Default to the latest term and its year if not specified
    latest_term = get_current_term()
    if not selected_term_id:
        selected_term_id = latest_term.id if latest_term else None
    if not selected_year:
        selected_year = latest_term.start_date.year if latest_term else None

    # Filter attendance data for the selected term and year
    attendance_data = []
    attendance_summary = {'total_present': 0, 'total_absent': 0, 'percentage': 0}

    if selected_term_id and selected_year:
        attendance_records = Attendance.objects.filter(
            student=student,
            term_id=selected_term_id,
            date__year=selected_year
        ).order_by('date')

        # Prepare attendance data and calculate statistics
        attendance_data = [{'date': record.date, 'present': record.is_present} for record in attendance_records]
        total_present = attendance_records.filter(is_present=True).count()
        total_days = attendance_records.count()
        total_absent = total_days - total_present
        attendance_summary = {
            'total_present': total_present,
            'total_absent': total_absent,
            'percentage': (total_present / total_days * 100) if total_days > 0 else 0,
        }

    # Prepare context
    context = {
        'student': student,
        'terms': terms,
        'years': years,
        'attendance_data': attendance_data,
        'attendance_summary': attendance_summary,
        'selected_term_id': selected_term_id,
        'selected_year': selected_year,
        'document_form': document_form,  # Pass the form for document upload
        'documents': student.documents.all(),  # Display all uploaded documents
    }
    return render(request, 'students/student-details.html', context)










def delete_document(request, document_id):
    document = get_object_or_404(StudentDocument, pk=document_id)
    student_id = document.student.id
    document.delete()
    messages.success(request, "Document deleted successfully.")
    return redirect('student_details', id=student_id)



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
