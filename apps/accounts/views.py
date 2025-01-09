import json
import os
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Q
from django.db.models.expressions import result
from django.db.models.functions.datetime import TruncMonth
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML, CSS

from School import settings
from apps.accounts import models
from apps.accounts.forms import ExpenseForm, FeeStructureForm
# from apps.accounts.forms import FeeStructureForm, ExpenseForm, InvoiceForm, InvoiceItemFormSet
from apps.accounts.models import FeeRecord, FeePayment, FeeStructure, Installment, Expense, Invoice, Customer
from apps.accounts.render import Render
from apps.management.models import Term, Institution
from apps.students.models import Student, StudentParent, Grade

import json
from django.shortcuts import render
#
from apps.students.views import get_current_term


# from apps.students.views import active_students


def update_student_fee(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_current_term()  # Assuming active term is marked `active=True`

    # Handle GET request to render the form
    if request.method == "GET":
        # Fetch the fee record for the student and term
        fee_record, created = FeeRecord.objects.get_or_create(student=student, term=term)
        return render(request, "accounts/additional_fee.html", {
            "student": student,
            "term": term,
            "fee_record": fee_record
        })

    # Handle POST request to update fees
    if request.method == "POST":
        fee_type = request.POST.get('fee_type')
        amount = Decimal(request.POST.get('amount', '0'))
        action = request.POST.get('action', 'activate')  # 'activate' or 'deactivate'

        # Fetch the fee record for the student and term
        fee_record, created = FeeRecord.objects.get_or_create(student=student, term=term)

        # Update or deactivate the fee
        if fee_type == "Transport fee":
            if action == "deactivate":
                fee_record.transport_fee = 0
                fee_record.transport_active = False
            else:
                fee_record.transport_fee = amount
                fee_record.transport_active = True

        elif fee_type == "Lunch Fees":
            if action == "deactivate":
                fee_record.lunch_fee = 0
                fee_record.lunch_active = False
            else:
                fee_record.lunch_fee = amount
                fee_record.lunch_active = True

        elif fee_type == "Remedial Fees":
            if action == "deactivate":
                fee_record.remedial_fee = 0
                fee_record.remedial_active = False
            else:
                fee_record.remedial_fee = amount
                fee_record.remedial_active = True

        # Save the record and recalculate totals
        fee_record.save()

        # Provide success message based on the action
        if action == "deactivate":
            messages.success(request, f"{fee_type} has been deactivated successfully.")
        else:
            messages.success(request, f"{fee_type} updated successfully.")

        return redirect('students_with_balances')

    # Fallback in case the method is not handled
    return redirect('students_with_balances')


# term fee rollover after every term
def start_new_term_with_rollover(new_term):
    with transaction.atomic():
        # Fetch all active students
        active_students = Student.objects.filter(status="active")
        update_count = 0

        for student in active_students:
            # Fetch the student's grade
            student_grade = student.grade

            # Skip if a fee record for the new term already exists
            if FeeRecord.objects.filter(student=student, term=new_term).exists():
                continue

            # Fetch the fee structure for the grade and term
            fee_structure = FeeStructure.objects.filter(grade=student_grade, term=new_term).first()

            term_fee = fee_structure.tuition_fee if fee_structure else Decimal(0)
            transport_fee = fee_structure.transport_fee if fee_structure else Decimal(0)
            lunch_fee = fee_structure.lunch_fee if fee_structure else Decimal(0)
            remedial_fee = fee_structure.remedial_fee if fee_structure else Decimal(0)

            # Fetch the latest fee record to check for active fees and balances
            latest_fee_record = FeeRecord.objects.filter(
                student=student,
                term__start_date__lt=new_term.start_date  # Only consider terms before the new term
            ).order_by('-term__start_date').first()

            if latest_fee_record:
                print(f"Fetched latest fee record for term: {latest_fee_record.term.name}")
            else:
                print(f"No previous fee record found for student: {student.first_name}")

            # Initialize previous balance and credit balance
            previous_balance = Decimal(0)
            credit_balance = Decimal(0)

            if latest_fee_record:
                # Carry over active fees (transport, lunch, remedial)
                if latest_fee_record.transport_active:
                    transport_fee = latest_fee_record.transport_fee
                if latest_fee_record.lunch_active:
                    lunch_fee = latest_fee_record.lunch_fee
                if latest_fee_record.remedial_active:
                    remedial_fee = latest_fee_record.remedial_fee

                # Add previous balance and credit from the latest fee record
                previous_balance = latest_fee_record.calculate_balance() if latest_fee_record else Decimal(0)
                credit_balance = latest_fee_record.calculate_overpayment()

                # Log previous balance and overpayment
                print(f"Previous balance carried over: {previous_balance}")
                print(f"Previous credit balance: {credit_balance}")

            # Calculate total additional fees (transport, lunch, remedial) for the new term
            total_additional_fees = transport_fee + lunch_fee + remedial_fee

            # Calculate the total fee for the new term, including previous balance and overpayment
            total_fee_for_new_term = term_fee + total_additional_fees + previous_balance - credit_balance

            # Log total fee for the new term
            print(f"Total fee for the new term (including previous balance and overpayment): {total_fee_for_new_term}")

            # Determine the initial balance and overpayment
            initial_balance = max(total_fee_for_new_term, Decimal(0))
            initial_overpayment = max(-total_fee_for_new_term, Decimal(0))

            # Create the new fee record for the new term
            FeeRecord.objects.create(
                student=student,
                term=new_term,
                tuition_fee=term_fee,
                transport_fee=transport_fee,
                lunch_fee=lunch_fee,
                remedial_fee=remedial_fee,
                total_fee=total_fee_for_new_term,
                paid_amount=Decimal(0),  # Reset the paid amount for the new term
                balance=initial_balance,  # Ensure the balance is correctly set
                overpayment=initial_overpayment,  # Initial overpayment
                due_date=new_term.end_date,
                transport_active=latest_fee_record.transport_active if latest_fee_record else False,
                lunch_active=latest_fee_record.lunch_active if latest_fee_record else False,
                remedial_active=latest_fee_record.remedial_active if latest_fee_record else False,
            )

            update_count += 1

    return {"updated_students": update_count}


def start_new_term_with_rollover_view(request):
    if request.method == "POST":
        term_id = request.POST.get("term_id")

        try:
            # Fetch the term, ensuring only one is selected
            new_term = Term.objects.filter(id=term_id).first()
            if not new_term:
                messages.error(request, "The selected term does not exist.")
                return redirect("students_with_balances")

            result = start_new_term_with_rollover(new_term)

            if result["updated_students"] > 0:
                messages.success(request,
                                 f"Successfully rolled over {result['updated_students']} students to {new_term.name}")
            else:
                messages.warning(
                    request,
                    "No students were updated. Please check fee structures and student status."
                )
        except Term.DoesNotExist:
            messages.error(request, "The selected term does not exist.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
        return redirect("students_with_balances")
    else:
        terms = Term.objects.all()
        return render(request, "accounts/start_term_fees.html", {"terms": terms})


@csrf_exempt
def fetch_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        timeframe = data.get('timeframe')

        # Filter data based on the selected timeframe
        if timeframe == 'today':
            start_date = now().date()
        elif timeframe == 'last_month':
            start_date = now() - timedelta(days=30)
        elif timeframe == 'last_year':
            start_date = now() - timedelta(days=365)
        else:
            return JsonResponse({'error': 'Invalid timeframe'}, status=400)

        # Fetch data from your model (example: FeePayment)
        from apps.accounts.models import FeePayment
        total_amount = FeePayment.objects.filter(date__gte=start_date).aggregate(Sum('amount'))['amount__sum'] or 0

        return JsonResponse({'total_amount': total_amount})


@login_required
def fee_structure_list(request):
    fee_structures = FeeStructure.objects.all()
    return render(request, 'accounts/fees-structure.html', {'fee_structures': fee_structures})


# View to Add a Fee Structure
@login_required
def add_fee_structure(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Structure added successfully!")
            return redirect('fee_structure_list')  # Redirect to the fee structure list page
    else:
        form = FeeStructureForm()
    return render(request, 'accounts/add-fee-strusture.html', {'form': form})


# View to Edit a Fee Structure
@login_required
def edit_fee_structure(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee Structure updated successfully!")
            return redirect('fee_structure_list')  # Redirect to the fee structure list page
    else:
        form = FeeStructureForm(instance=fee_structure)
    return render(request, 'accounts/update_fee_structure.html', {'form': form, 'fee_structure': fee_structure})


@login_required
def student_payments(request, id):
    student = get_object_or_404(Student, pk=id)

    # Fetch all payments for the student, ordered by payment date
    payments = FeePayment.objects.filter(fee_record__student=student).order_by('date')

    # Initialize the payment details list
    payment_details = []

    # Fetch all fee records for the student, ordered by term
    fee_records = FeeRecord.objects.filter(student=student).order_by('term__start_date')

    for fee_record in fee_records:
        # Start with the total fee for the current fee record
        # total_fee = fee_record.calculate_total_fee()
        total_fee = fee_record.total_fee
        paid_so_far = 0  # Track cumulative payments for this fee record

        # Filter payments related to this fee record
        related_payments = payments.filter(fee_record=fee_record)

        for payment in related_payments:
            paid_so_far += payment.amount  # Increment cumulative payments
            fee_balance = total_fee - paid_so_far   # Calculate the remaining balance

            payment_details.append({
                'fee_record': fee_record,
                'date': payment.date,
                'total_fee': total_fee,
                'amount': payment.amount,
                'balance': fee_balance,
                'payment_method': payment.payment_method,
            })

    context = {
        'student': student,
        'payments': payment_details,
    }
    return render(request, 'accounts/payment_records.html', context)


# fee_collection_filter
@login_required
def fee_collection_filter(request):
    # Get the filter parameters from the GET request
    selected_grade = request.GET.get('grade', None)
    # selected_class = request.GET.get('class', None)

    # Fetch all grades to populate the dropdown
    grades = Grade.objects.all()
    print("Grades fetched:", grades)  # Debugging: Print grades in the console

    # classes = Student.objects.values_list('class', flat=True).distinct()
    # print("Classes fetched:", classes)  # Debugging: Print classes in the console

    # Start with all students
    students = Student.objects.all()

    # Apply filtering by grade and class if selected
    if selected_grade:
        students = students.filter(grade__name=selected_grade)  # Ensure Student has a grade field
    # if selected_class:
    #     students = students.filter(class__exact=selected_class)

    # Order the students by admission number (ascending)
    students = students.order_by('admission_number')

    context = {
        'students': students,
        'grades': grades,
        # 'classes': classes,
        'selected_grade': selected_grade,
        # 'selected_class': selected_class,
    }

    return render(request, 'accounts/students_with_balances.html', context)


@login_required
def students_fee_records(request):
    # Get all fee records with their total paid amount
    fee_records = FeeRecord.objects.select_related('student').all()

    return render(request, 'accounts/students_fee_records.html', {
        'fee_records': fee_records,
    })


@login_required
def collect_fees(request, fee_record_id):
    fee_record = get_object_or_404(FeeRecord, id=fee_record_id)
    previous_record = fee_record.get_previous_record()
    previous_term = previous_record.term.name if previous_record else "No previous Term Fee",

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        reference = request.POST.get('reference')

        # Save payment
        FeePayment.objects.create(
            fee_record=fee_record,
            amount=amount,
            reference=reference,
        )
        # Update total paid
        fee_record.paid_amount += amount
        fee_record.save()

        # Check for overpayment
        if fee_record.paid_amount > fee_record.calculate_total_fee():
            overpaid_amount = fee_record.paid_amount - fee_record.calculate_total_fee()
            messages.warning(
                request,
                f"Payment exceeds the total fee by {overpaid_amount:.2f}. Please verify."
            )

        return redirect('students_with_balances')  # Redirect to the list of students with balances

    return render(request, 'accounts/collect_fees.html', {'fee_record': fee_record, "previous_term": previous_term})


def generate_receipt(request, fee_record_id):
    # Fetch the current fee record
    fee_record = get_object_or_404(FeeRecord, id=fee_record_id)
    institution = Institution.objects.last()

    # Fetch the previous term's record
    previous_record = fee_record.get_previous_record()

    # Calculate balances
    previous_balance = previous_record.calculate_balance() if previous_record else 0
    current_balance = fee_record.calculate_balance()
    final_balance = current_balance + previous_balance

    # Get active fees
    active_fees = [
        {"description": "Tuition Fee", "amount": fee_record.tuition_fee, "active": True},
        {"description": "Transport Fee", "amount": fee_record.transport_fee, "active": fee_record.transport_active},
        {"description": "Lunch Fee", "amount": fee_record.lunch_fee, "active": fee_record.lunch_active},
        {"description": "Remedial Fee", "amount": fee_record.remedial_fee, "active": fee_record.remedial_active},
    ]
    active_fees = [fee for fee in active_fees if fee["active"]]

    # Fetch the parents associated with the student through StudentParent
    student = fee_record.student
    student_parents = StudentParent.objects.filter(student=student)

    parent_details = [
        {
            "first_name": parent.parent.first_name,
            "last_name": parent.parent.last_name,
            "contact_number": parent.parent.mobile,
            "email": parent.parent.email,
            "relationship": parent.relationship,
        }
        for parent in student_parents
    ]

    guardian_names = ", ".join(
        [f"{parent['first_name']} {parent.get('last_name', '')}".strip() for parent in parent_details]
    ) if parent_details else "N/A"

    # Fetch the most recent payment for the fee record (if available)
    recent_payment = fee_record.payments.order_by('-date').first()

    # Prepare context
    context = {
        "fee_record": fee_record,
        "student_first_name": fee_record.student.first_name,
        "student_last_name": fee_record.student.last_name,
        "student_grade": fee_record.student.grade.grade,
        "guardian_name": guardian_names,
        "parent_details": parent_details,
        "term_name": fee_record.term.name,
        "payment_mode": recent_payment.payment_method if recent_payment else "N/A",
        "payment_date": recent_payment.date if recent_payment else "N/A",
        "payment_reference": recent_payment.reference if recent_payment else "N/A",
        "previous_balance": previous_balance,
        "current_balance": current_balance,
        "final_balance": final_balance,
        "active_fees": active_fees,
        "subtotal": sum(fee["amount"] for fee in active_fees),
        "payments_made": fee_record.paid_amount,
        "overpayment": fee_record.calculate_overpayment(),
        "institution": institution,
    }

    return render(request, "accounts/receipt.html", context)


def generate_pdf_receipt(request, fee_record_id):
    # Fetch the fee record
    fee_record = get_object_or_404(FeeRecord, id=fee_record_id)

    # Fetch the parents associated with the student
    student = fee_record.student
    student_parents = StudentParent.objects.filter(student=student)
    institution = Institution.objects.last()

    parent_details = [
        {
            "first_name": parent.parent.first_name,
            "last_name": parent.parent.last_name,
            "contact_number": parent.parent.mobile,
            "email": parent.parent.email,
            "relationship": parent.relationship,
        }
        for parent in student_parents
    ]

    guardian_names = ", ".join(
        [f"{parent['first_name']} {parent.get('last_name', '')}".strip()
         for parent in parent_details]
    ) if parent_details else "N/A"

    # Context for the receipt template
    context = {
        "fee_record": fee_record,
        "student_first_name": fee_record.student.first_name,
        "student_last_name": fee_record.student.last_name,
        "student_grade": fee_record.student.grade,
        "guardian_name": guardian_names,
        "term_name": fee_record.term.name,
        "tuition_fee": fee_record.tuition_fee,
        "transport_fee": fee_record.transport_fee if fee_record.transport_active else 0,
        "lunch_fee": fee_record.lunch_fee if fee_record.lunch_active else 0,
        "remedial_fee": fee_record.remedial_fee if fee_record.remedial_active else 0,
        "previous_balance": fee_record.previous_balance(),
        "payments_made": fee_record.paid_amount,
        "total_fee": fee_record.total_fee,
        "balance": fee_record.balance,
        "overpayment": fee_record.overpayment,
        "institution": institution,
    }

    return Render.render('accounts/receipt.html',context) # Render the receipt template for PDF generation



@login_required
def assign_fees_to_grade(request, grade_id):
    # Fetch the grade
    grade = get_object_or_404(Class, id=grade_id)

    # Fetch the current term
    current_term = Term.objects.filter(start_date__lte=request.today, end_date__gte=request.today).first()
    if not current_term:
        return redirect("term_list")  # Redirect if no active term

    # Fetch the fee structure for the grade and term
    try:
        fee_structure = FeeStructure.objects.get(grade=grade, term=current_term)
        term_fee = fee_structure.tuition_fee
    except FeeStructure.DoesNotExist:
        return redirect("fee_structure_list")  # Redirect if fee structure not set

    # Get all students in the grade
    students = Student.objects.filter(grade=grade)

    for student in students:
        # Check if FeeRecord already exists for the current term and student
        fee_record, created = FeeRecord.objects.get_or_create(
            student=student,
            term=current_term,
            defaults={
                "total_fee": term_fee,
                "paid_amount": Decimal("0.00"),
                "balance": term_fee
            }
        )

        if not created:
            # Update existing record if necessary
            fee_record.total_fee = term_fee
            fee_record.balance = term_fee - fee_record.paid_amount
            fee_record.save()

    return redirect("success_page")  # Redirect to confirmation page


# handling fees paid through mpesa
@csrf_exempt
def mpesa_payment_callback(request):
    if request.method == 'POST':
        mpesa_data = json.loads(request.body)

        # Extract M-Pesa details
        admission_number = mpesa_data.get('AccountReference')
        amount = Decimal(mpesa_data.get('TransAmount'))
        transaction_id = mpesa_data.get('TransID')

        # Find the FeeRecord for the student
        try:
            fee_record = FeeRecord.objects.get(student__admission_number=admission_number)

            # Update the balance
            fee_record.balance -= amount
            fee_record.save()

            # Log the installment
            Installment.objects.create(
                fee_record=fee_record,
                amount=amount,
                reference=transaction_id,
                payment_date=mpesa_data.get('TransTime'),
            )

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
        except FeeRecord.DoesNotExist:
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Admission Number not found"})
    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid Request"})


@login_required
def students_with_balances(request):

    # Get all fee records with their total paid amount
    fee_records = FeeRecord.objects.select_related('student').filter(student__status="Active")

    # Filter students with outstanding balances
    students_with_balances = []
    for fee_record in fee_records:
        current_balance = fee_record.calculate_balance()
        if fee_record.calculate_balance() > 0:
            students_with_balances.append(fee_record)

    return render(request, 'accounts/students_with_balances.html', {
        'students_with_balances': students_with_balances,
    })


def fee_record_view(request, fee_record_id):
    fee_record = get_object_or_404(FeeRecord, id=fee_record_id)
    return render(request, 'accounts/additional_fee.html', {'fee_record': fee_record})


def update_student_fee_structure(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    term_id = request.POST.get("term_id")
    if request.method == "POST":
        student_id = student
        transport_fee = float(request.POST.get("transport_fee", 0))
        lunch_fee = float(request.POST.get("lunch_fee", 0))
        remedial_fee = float(request.POST.get("remedial_fee", 0))
        withdraw_transport = request.POST.get("withdraw_transport", False)
        withdraw_remedial = request.POST.get("withdraw_remedial", False)

        try:
            # Get the current term
            current_term = get_current_term()
        except Exception as e:
            return HttpResponse(f"Error: {e}")  # Handle no active term scenario gracefully

        # Fetch the student's fee record for the current term
        fee_record = get_object_or_404(FeeRecord, student_id=student_id, term=current_term)

        # Update the fees
        fee_record.transport_fee = 0 if withdraw_transport else transport_fee
        fee_record.remedial_fee = 0 if withdraw_remedial else remedial_fee
        fee_record.lunch_fee = lunch_fee
        fee_record.balance = fee_record.calculate_balance()
        fee_record.overpayment = fee_record.calculate_overpayment()
        fee_record.save()
        messages.success(request, f"Fee record updated successfully!")

        return redirect("students_with_balances")
    return render(request, "accounts/additional_fee.html")


def all_students_fee_records(request):
    # Get all fee records
    fees_record = FeeRecord.objects.all()

    # prepare statuses
    all_students_fee_records = []
    for record in fees_record:
        balance_due = record.calculate_balance()
        if balance_due == 0:
            status = "Cleared"
        elif balance_due > 0:
            status = "Unpaid"
        else:
            status = "Overpayment"
        all_students_fee_records.append({
            "record": record,
            "status": status,
        })
        # pass data to the template

    return render(request, 'accounts/all_fee_records.html', {"fee_record": all_students_fee_records})


# def update_transport_lunch(request):
#     # check if it's a POST request to update the students
#     if request.method == "POST":
#         # Get the list of selected students IDS
#         selected_students_ids = request.POST.getlist('selected_students')
#
#         # Get transport and lunch fees from the form
#         transport_fee = float(request.POST.get("transport_fee", 0))
#         lunch_fee = float(request.POST.get("lunch_fee", 0))
#
#         # Get checkbox values for transport and lunch
#         is_transport_selected = request.POST.get("is_transport_selected", False) == 'on'
#         is_lunch_selected = request.POST.get("is_lunch_selected", False) == 'on'
#
#         # Update the selected student's fee records
#         for student_id in selected_students_ids:
#             student = get_object_or_404(Student, id=student_id)
#             if student.status == "Active" and not student.sponsored:
#                 fee_record = FeeRecord.objects.filter(
#                     student=student).last()  # Assuming one fee record per student per term
#
#                 if fee_record:
#                     # update transport and lunch fees based on selected checkboxes
#                     if is_transport_selected:
#                         fee_record.transport_fee = transport_fee
#                     else:
#                         fee_record.transport_fee = 0
#                     if is_lunch_selected:
#                         fee_record.lunch_fee = lunch_fee
#                     else:
#                         fee_record.lunch_fee = 0
#
#                     # save the updated FeeRecord
#                     fee_record.save()
#         # redirect to a success page back o the student list
#         return redirect('students_with_balances')
#     # if the request method is Get ,retrieve all students to display in the form
#     # students = Student.objects.all
#     return render(request, 'accounts/students_with_balances.html', {'students': students})


# handle overpayments and credit them to next term
def get_students_with_overpayments():
    students_with_balances = FeeRecord.objects.select_related('student')

    students_with_overpayments = []

    for fee_record in students_with_balances:
        # check overpayments
        balance_due = fee_record.calculate_balance()

        # add to overpayment lists
        if fee_record.paid_amount > fee_record.calculate_total_fee():
            overpayment = fee_record.paid_amount - fee_record.total_fee
            students_with_overpayments.append({
                'student': fee_record.student,
                'overpayment': overpayment,
                'term': fee_record.term,
                'balance_due': balance_due
            })

    return students_with_overpayments


def students_with_overpayments_view(request):
    students_with_overpayments = get_students_with_overpayments()
    return render(request, 'accounts/overpayment_list.html', {"student_with_overpayments": students_with_overpayments})


@login_required
def search_student_fees(request):
    search_term = request.GET.get('search_fee', '').strip()  # Get the search term from the query parameters

    fee_records = FeeRecord.objects.select_related('student').filter(student__status="Active")

    # Filter students with outstanding balances
    students_with_balances = [
        fee_record for fee_record in fee_records if fee_record.calculate_balance() > 0
    ]

    # Apply the search filter if there's a search term
    if search_term:
        students_with_balances = students_with_balances.filter(
            Q(student__first_name__icontains=search_term) |
            Q(student__last_name__icontains=search_term) |
            Q(student__grade__name__icontains=search_term) |
            Q(student__admission_number__icontains=search_term)
        )

    context = {
        'students_with_balances': students_with_balances,
    }
    return render(request, 'accounts/students_with_balances.html', context)


@login_required
def search_student(request):
    search_term = request.GET.get('search_student', '').strip()  # Get and sanitize the search term

    students = Student.objects.all()
    # Fetch students based on the search term
    if search_term:
        students = students.filter(
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term) |
            Q(grade__name__icontains=search_term) |
            Q(admission_number__icontains=search_term)
        )
    # else:
    #     # If no search term, return all students or none based on your requirements
    #     students = Student.objects.all()

    context = {
        'students': students,
        # 'search_term': search_term,  # Include the search term for template reuse
    }
    return render(request, 'students/students.html', context)


# Define the function to get total revenue for the current year

def get_total_revenue():
    current_year = date.today().year

    # Get all FeePayments for the current year grouped by month
    fee_payments = FeePayment.objects.filter(date__year=current_year).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_revenue=Sum('amount')
    )

    # Calculate the total revenue
    total_revenue = sum(payment['total_revenue'] or 0 for payment in fee_payments)
    return total_revenue


def expense_view(request):
    # Handle form submission to add a new expense
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new expense
            return redirect('expense_view')  # Redirect to the same page to show the updated list

    # Get all expenses from the database
    expenses = Expense.objects.all().order_by('-date')  # Order by date (latest first)

    # Calculate total expenses
    total_expenses = sum(expense.amount for expense in expenses)

    # Get the total revenue
    total_revenue = get_total_revenue()  # Call without request
    net_revenue = total_revenue - total_expenses

    # Prepare the form for the template
    form = ExpenseForm()

    # Pass the data to the template
    return render(request, 'accounts/expense.html', {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'total_revenue': total_revenue,
        'net_revenue': net_revenue,
        'form': form,
    })


@login_required
def delete_expense(request, expense_id):
    # Handle deletion of an expense
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    return redirect('expense_view')  # Redirect back to the expense view


def teacher_dash(request):
    return render(request, 'Home/teacher_dashboard.html')


def invoice_list(request):
    invoices = Invoice.objects.prefetch_related('items').all()  # Prefetch related invoice items
    return render(request, 'accounts/invoice_list.html', {'invoices': invoices})


def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, "accounts/view_invoice.html", {"invoice": invoice})


def update_fee_component(request, fee_record_id, component):
    fee_record = get_object_or_404(FeeRecord, id=fee_record_id)

    if request.method == "POST":
        new_value = request.POST.get("value", 0)
        if component == "transport_fee":
            fee_record.transport_fee = new_value
        elif component == "lunch_fee":
            fee_record.lunch_fee = new_value
        elif component == "remedial_fee":
            fee_record.remedial_fee = new_value

        fee_record.save()
        return JsonResponse({
            "success": True,
            "balance": fee_record.balance,
            "overpayment": fee_record.overpayment
        })
