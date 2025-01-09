from collections import defaultdict
from datetime import date, timedelta, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.transaction import atomic

from django.shortcuts import render, redirect, get_object_or_404


from apps.accounts.models import FeeStructure, FeeRecord
from apps.management.models import Term, SubjectMark, ReportCard
from apps.students.forms import StudentForm, PromoteStudentsForm, SendSMSForm
# from apps.students.forms import StudentForm
from apps.students.models import Student, Parent, Class, StudentParent
from apps.students.utils import MobileSasaAPI


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
        #get list of selected student
        selected_students = request.POST.getlist("selected_students") #grabs list of selected student

        if not selected_students:
            messages.error(request,"No students selected.")
            return redirect('active_students')
        try:
            #update status of selected to graduate
            with transaction.atomic():
                students = Student.objects.filter(id__in=selected_students,status="Active")
                students.update(status="graduated")
            messages.success(request,f"Successfully updated {students.count()} student(s) to 'Graduated'. ")
            return redirect("active_students")
        except Exception as e:
            messages.error(request,f"An error occurred: {e}")
            return redirect("active_students")
    else:
        #handle get request(students)
        students_active = Student.objects.filter(status="active")
        return  render(request,"students/All-students.html", {"students_active": students_active})



def reverse_student_status(request):
    if request.method == "POST" :
        #Get the list of selected student IDs
        selected_students = request.POST.getlist("selected_students")

        if not  selected_students:
            messages.error(request,"No students selected")
            return  redirect("active_students")
        try:
            #revert the status of selected students to active
            with transaction.atomic():
                students = Student.objects.filter(id__in=selected_students,status="graduated")
                students.update(status="Active")
            messages.success(request,f"Successfully reverted {students.count()} students to 'Active")
            return redirect("active_students")
        except Exception as e:
            messages.error(request,f"An error occurred: {e}")
            return redirect("active_students")
    else:
        #if get method show graduated students
        students_graduated = Student.objects.filter(status="graduated")
        return render(request,'students/students_graduated.html',{"students_graduated":students_graduated})




# promote students to next class and the completed students marked as graduated
def promote_students():
    from django.db.models import Max
    from django.utils.timezone import now
    # fetching the max grade -grade 9/form 4
    max_level = Class.objects.aggregate(max_level=Max('level'))['max_level']

    if max_level is None:
        return {"students_promoted": 0, "students_graduated": 0}  # No classes available

    students_promoted_count = 0

    # promote students
    with transaction.atomic():
        current_year = datetime.now().year
        students_to_promote = Student.objects.filter(status='active', Class__level__lt=max_level,
                                                     ).exclude(last_promoted__year=current_year)   # Exclude students already promoted this year


        for student in students_to_promote:
            next_class = Class.objects.filter(level=student.grade.level + 1).first()
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
        form = PromoteStudentsForm(request.POST)
        if form.is_valid():
            try:
                result = promote_students()
                messages.success(
                    request,
                    f"{result['students_promoted']} students promoted and {result['students_graduated']} students graduated successfully."
                )
            except Exception as e:
                messages.error(request, f"An error occurred during promotion: {e}")
        else:
            messages.error(request, "Please confirm promotion before proceeding.")
        return redirect("students")
    else:
        form = PromoteStudentsForm()
    return render(request, "students/confirm_promotion.html", {"form": form})


#current term
def get_current_term():
    # Get today's date
    today = date.today()

    try:
        # Fetch the current term from the database based on today's date
        current_term = Term.objects.get(start_date__lte=today, end_date__gte=today)
        return current_term
    except Term.DoesNotExist:
        raise Exception(
            "No active term found for today's date. Please ensure terms are correctly set up in the database.")


print(get_current_term())


def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()  # Save the student instance
            try:
                # Fetch the current term
                current_term = get_current_term()

                # Fetch the fee structure for the student's grade and current term
                grade = student.grade  # Assuming 'Class' is the field for the grade
                if grade and current_term:
                    fee_structure = FeeStructure.objects.filter(grade=grade, term=current_term).first()

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
                            f"Fee record created for {student.first_name} {student.last_name} with total fee {fee_structure.tuition_fee}."
                        )
                    else:
                        messages.warning(
                            request,
                            f"No fee structure found for grade {grade.name} in term {current_term.name}. Please set up the fee structure."
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
def student_details(request, id):
    student = get_object_or_404(Student, pk=id)
    report_cards = ReportCard.objects.filter(student=student)
    subject_marks = SubjectMark.objects.filter(student=student)
    student_parents = StudentParent.objects.filter(student=student)

    # Optionally, fetch the current or latest term's report card
    latest_term = get_current_term()
    latest_report_card = None
    if latest_term:
        latest_report_card = report_cards.filter(term=latest_term).first()

    # Calculate total marks and rank for each report card
    report_card_details = []
    for report_card in report_cards:
        total_marks = report_card.total_marks()  # Assuming this method exists
        rank = report_card.student_rank()  # Assuming this method exists
        report_card_details.append({
            'report_card': report_card,
            'total_marks': total_marks,
            'rank': rank,
        })

    # Handle SMS form submission
    if request.method == "POST":
        form = SendReminderForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]

            # Fetch the selected parent
            parent_id = request.POST.get("parent_id")
            parent = get_object_or_404(StudentParent, id=parent_id).parent

            # Use MobileSasaAPI to send the SMS
            api = MobileSasaAPI()
            response = api.send_single_sms(str(parent.mobile), message)

            if response and response.get("status"):
                messages.success(request, "SMS sent successfully!")
            else:
                messages.warning(request, "Failed to send SMS.")
            return redirect("student_details", id=student.id)
    else:
        form = SendReminderForm()

    context = {
        'student': student,
        'report_cards': report_card_details,
        'subject_marks': subject_marks,
        'latest_report_card': latest_report_card,
        'student_parents': student_parents,
        'form': form,
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
                student = form.save()

                # Handle parent assignments if they were updated
                if 'parents' in request.POST:
                    parent_ids = request.POST.getlist('parents')
                    parent_objects = Parent.objects.filter(id__in=parent_ids)
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
