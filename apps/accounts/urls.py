from django.urls import path
from . import views

urlpatterns = [
    path('students-with-balances/', views.students_with_balances, name='students_with_balances'),
    path('collect-fees/<int:fee_record_id>/', views.collect_fees, name='collect_fees'),
    path('students/<int:id>/payments/', views.student_payments, name='student_payments'),
    path('fee_collection_filter/', views.fee_collection_filter, name='fee_collection_filter'),
    path('search_student_fees/', views.search_student_fees, name='search_student_fees'),
    path('students/search', views.search_student, name='search_student'),

]
