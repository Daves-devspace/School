from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db.models import Sum
from django.db.models.functions.datetime import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, redirect

from apps.accounts.models import FeePayment
from apps.management.models import Term
from apps.students.models import Student
from apps.teachers.models import Teacher, Department


# Create your views here.
@login_required
def home(request):
    current_year = date.today().year
    total_revenue = FeePayment.objects.filter(date__year=current_year).aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_departments = Department.objects.count()

    return render(request,'Home/index.html',{"total_revenue": total_revenue,
                                             "total_students": total_students,
                                             "total_teachers": total_teachers,
                                             "total_departments": total_departments,
                                             'current_year': current_year,
                                             })





def login_user(request):
    if request.method == 'GET':
        return render(request, 'Home/login_form.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username,password=password)
        if user:
            login(request,user)
            messages.success(request,'You are logged in!')
            return redirect('home')
        messages.warning(request,'Invalid username or password')
        return redirect('login')

@login_required
def logout_user(request):
    logout(request)
    return render(request,'Home/login_form.html')

#def login_form(request):

def website_page(request):
    return render(request,'Home/website/index.html')






