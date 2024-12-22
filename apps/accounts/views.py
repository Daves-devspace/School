import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions.datetime import TruncMonth
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from apps.accounts import models
from apps.accounts.forms import  ExpenseForm, FeeStructureForm
# from apps.accounts.forms import FeeStructureForm, ExpenseForm, InvoiceForm, InvoiceItemFormSet
from apps.accounts.models import FeeRecord, FeePayment, FeeStructure, Installment, Expense, Invoice, Customer
from apps.management.models import Term
from apps.students.models import Class, Student

import json
from django.shortcuts import render



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

    # Fetch all payments for the student, ordered by payment date, using the fee_records related_name
    payments = FeePayment.objects.filter(fee_record__student=student).order_by('date')

    # Initialize the balance with the total fee for the student
    fee_record = student.fee_records.first()  # each student has one fee record
    total_fee = fee_record.total_fee if fee_record else 0
    balance = total_fee

    # Loop through the payments and calculate the balance after each payment
    payment_details = []
    for payment in payments:
        balance -= payment.amount
        payment_details.append({
            'fee_record': payment.fee_record,
            'date': payment.date,
            'amount': payment.amount,
            'balance': balance
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
    grades = Class.objects.all()
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
        if fee_record.paid_amount > fee_record.total_fee:
            overpaid_amount = fee_record.paid_amount - fee_record.total_fee
            messages.warning(
                request,
                f"Payment exceeds the total fee by {overpaid_amount:.2f}. Please verify."
            )

        return redirect('students_with_balances')  # Redirect to the list of students with balances

    return render(request, 'accounts/collect_fees.html', {'fee_record': fee_record})


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
        term_fee = fee_structure.amount
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
    fee_records = FeeRecord.objects.select_related('student').all()

    # Filter students with outstanding balances
    students_with_balances = []
    for fee_record in fee_records:
        if fee_record.balance_due() > 0:
            students_with_balances.append(fee_record)

    return render(request, 'accounts/students_with_balances.html', {
        'students_with_balances': students_with_balances,
    })


@login_required
def search_student_fees(request):
    search_term = request.GET.get('search_fee', '').strip()  # Get the search term from the query parameters

    # Initialize the queryset for the balances
    students_with_balances = FeeRecord.objects.all()  # Assuming FeeRecord is the model for the records

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


#
# def create_invoice(request):
#     if request.method == 'POST':
#         invoice_form = InvoiceForm(request.POST)
#         item_formset = InvoiceItemFormSet(request.POST)
#         if invoice_form.is_valid() and item_formset.is_valid():
#             invoice = invoice_form.save()
#             items = item_formset.save(commit=False)
#             for item in items:
#                 item.invoice = invoice
#                 item.save()
#             return redirect('invoice_detail', pk=invoice.pk)
#         else:
#             return render(request, 'accounts/add_invoice.html', {
#                 'invoice_form': invoice_form,
#                 'item_formset': item_formset
#             })
#     else:
#         invoice_form = InvoiceForm()
#         item_formset = InvoiceItemFormSet()
#     return render(request, 'accounts/add_invoice.html', {
#         'invoice_form': invoice_form,
#         'item_formset': item_formset
#     })
#
# def create_invoice(request):
#     customers = Customer.objects.all()  # Fetch all customers from the database
#     if request.method == 'POST':
#         # Handle form submission here
#         pass
#     return render(request,'accounts/add_invoice.html',{'customers': customers})
def add_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # Save the invoice first (without saving the formset yet)
            invoice = form.save(commit=False)
            # Calculate the total_amount from formset
            total_amount = 0
            items = formset.save(commit=False)
            for item in items:
                item.invoice = invoice  # Link item to this invoice
                total_amount += item.total_price  # Add item total to invoice total_amount
            invoice.total_amount = total_amount
            invoice.save()

            # Save all items after the invoice is created
            for item in items:
                item.save()

            return redirect('invoice_preview', invoice_id=invoice.id)  # Redirect to preview

    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()


    return render(request, 'accounts/add_invoice.html', {'form': form, 'formset': formset})


# def download_invoice(request, invoice_id):
#     invoice = Invoice.objects.get(pk=invoice_id)
#     html = render_to_string('accounts/view_invoice.html', {'invoice': invoice})
#
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'
#     weasyprint.HTML(string=html).write_pdf(response)
#
#     return response
