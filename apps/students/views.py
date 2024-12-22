from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from apps.accounts.models import FeeStructure, FeeRecord
from apps.management.models import Term
from apps.students.forms import StudentForm
# from apps.students.forms import StudentForm
from apps.students.models import Student, Parent, Class, StudentParent


# Create your views here.
@login_required
def students(request):
    student_list = Student.objects.all()
    return render(request, "students/students.html", {"student_list": student_list})


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
                grade = student.Class  # Assuming 'Class' is the field for the grade
                if grade and current_term:
                    fee_structure = FeeStructure.objects.filter(grade=grade, term=current_term).first()

                    if fee_structure:
                        # Create the fee record for the student
                        FeeRecord.objects.create(
                            student=student,
                            term=current_term,
                            total_fee=fee_structure.amount,
                            paid_amount=0,
                            due_date=current_term.end_date
                        )
                        messages.success(
                            request,
                            f"Fee record created for {student.first_name} {student.last_name} with total fee {fee_structure.amount}."
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

@login_required
def student_details(request, id):
    student = Student.objects.get(pk=id)
    return render(request, 'students/student-details.html',
                  {'student': student})


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
