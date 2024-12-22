import json
from datetime import date, timedelta, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions.datetime import TruncMonth, ExtractYear
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django_daraja.mpesa.core import MpesaClient

from apps.accounts.models import FeePayment, Expense
from apps.management.forms import AddResultForm, SubjectForm
from apps.management.models import Term, Subject, Result, Teacher, TeacherSubject, ReportCard
from apps.students.models import Book, Transaction, Student, Payment, Class

# Create your views here.
from django.db.models import Avg, Sum, Count, Q

from apps.teachers.models import Department  # Revenue


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

# # Save Subject
# def save_subject(request):
#     if request.method == 'POST':
#         form = SubjectForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('view_subjects')  # Redirect to the subject list
#     else:
#         form = SubjectForm()
#     return render(request, 'subject_form.html', {'form': form})


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


# teachers adding results
@login_required
def add_results(request):
    if request.method == 'POST':
        form = AddResultForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            teacher_subject = form.cleaned_data['teacher_subject']
            term = form.cleaned_data['term']
            score = form.cleaned_data['score']

            # Check if result already exists
            existing_result = Result.objects.filter(
                student=student,
                teacher_subject=teacher_subject,
                term=term
            ).exists()

            if existing_result:
                messages.error(request, "Result already exists for this student, subject, and term.")
            else:
                Result.objects.create(
                    student=student,
                    teacher_subject=teacher_subject,
                    term=term,
                    score=score
                )
                messages.success(request, "Result added successfully!")
            return redirect('add_results')
    else:
        form = AddResultForm()

    return render(request, 'performance/add_results.html', {'form': form})


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
    grade = Grade.objects.get(id=grade_id)
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


# one student performance
# def student_performance(request, student_id):
#     results = Result.objects.filter(student_id=student_id).select_related('subject')
#     total_score = results.aggregate(total=Sum('score'))['total']
#
#     return render(request, 'performance/student_performance.html', {
#         'results': results,
#         'total_score': total_score,
#     })
# def student_performance(request, student_id, term_id):
#     student = Student.objects.get(id=student_id)
#     term = Term.objects.get(id=term_id)
#     performances = Performance.objects.filter(student=student, term=term)
#
#     return render(request, 'performance/student_performance.html', {
#         'student': student,
#         'term': term,
#         'performances': performances
#     })
@login_required
def student_results(request, student_id):
    student = Student.objects.get(id=student_id)
    results = Result.objects.filter(student=student)

    return render(request, 'performance/student_performance.html', {
        'student': student,
        'results': results
    })


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

# @login_required
# def gender_pie_data(request):
#     # Count boys and girls in your dataset
#     boys_count = Student.objects.filter(gender='Male').count()
#     girls_count = Student.objects.filter(gender='Female').count()
#
#     return JsonResponse({
#         "title": "Gender Ratio",
#         "data": {
#             "labels": ["Boys", "Girls"],
#             "datasets": [{
#                 "data": [boys_count, girls_count],
#                 "backgroundColor": ['#4e73df', '#ff6384'],  # Colors for boys and girls
#                 "hoverBackgroundColor": ['#2e59d9', '#e57373'],  # Hover colors
#                 "hoverBorderColor": "rgba(234, 236, 244, 1)",
#             }],
#         }
#     })


@login_required
def gender_pie_data(request):
    current_year = datetime.now().year

    boys_count = Student.objects.filter(gender="Male", joining_date__year=current_year).count()
    girls_count = Student.objects.filter(gender="Female", joining_date__year=current_year).count()

    return JsonResponse({
        "title": "Gender Ratio for the Year",
        "labels": ["Boys", "Girls"],
        "datasets": [{
            "data": [boys_count, girls_count],
            "backgroundColor": ["#0a3622", "#008374"],  # Deep green and teal for initial display
            "hoverBackgroundColor": ["#106b45", "#00a38d"],  # Brighter shades on hover
            "hoverBorderColor": "rgba(234, 236, 244, 1)",  # Light border on hover
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




def filter_results(request):
    classes = Class.objects.all()  # Replace with your class model
    terms = Term.objects.all()
    subjects = Subject.objects.all()

    students = None
    if request.GET:
        class_id = request.GET.get('class')
        term_id = request.GET.get('term')
        test = request.GET.get('test')
        subject_id = request.GET.get('subject')

        # Filter students based on class
        students = Student.objects.filter(Class_id=class_id)

    return render(request, 'performance/query_students.html', {
        'classes': classes,
        'terms': terms,
        'subjects': subjects,
        'students': students,
    })

def save_results(request,student_id):
    if request.method == "POST":
        student = get_object_or_404(Student, id=student_id)
        term = Term.objects.get(id=request.POST['term_id'])
        subject = Subject.objects.get(id=request.POST['subject_id'])
        test = request.POST['test']
        score = request.POST['score']

        # Save the result
        Result.objects.create(
            student=student,
            term=term,
            subject=subject,
            test_type=test,
            score=score,
        )
    return redirect('view_results')


def exam_list(request):
    return render(request,'performance/examlist.html')