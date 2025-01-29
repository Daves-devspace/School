from django.urls import path
from . import views

urlpatterns = [
    path('students-with-balances/', views.students_with_balances, name='students_with_balances'),
    path('students_with_overpayments_view/', views.students_with_overpayments_view, name='overpayments'),
    #path('adjust-fee/<int:student_id>/', views.manage_student_fee, name='adjust_fee'),
    path('update-student-fee/<int:student_id>/', views.update_student_fee, name='update_student_fee'),
    path('api/fee-record/<int:fee_record_id>/update/<str:component>/', views.update_fee_component,
         name='update_fee_component'),
    path('fee-record/<int:fee_record_id>/', views.fee_record_view, name='fee_record_view'),
    path('update_student_fee_structure/<int:student_id>/', views.update_student_fee_structure,
         name='update_fee_structure'),
    path('all_students_fee_records/', views.all_students_fee_records, name='all_records'),
    path('start_new_term_with_rollover_view/', views.start_new_term_with_rollover_view, name='start_new_term'),
    path('students_fee_records/', views.students_fee_records, name='students_fee_records'),

    path('collect-fees/<int:fee_record_id>/', views.collect_fees, name='collect_fees'),
    path('accounts/receipt/<int:fee_record_id>/', views.generate_receipt, name='generate_receipt'),
    path('accounts/generate-receipt/<int:fee_record_id>/', views.generate_pdf_receipt, name='generate_pdf_receipt'),
    path('students/<int:id>/payments/', views.student_payments, name='student_payments'),
    path('fee_collection_filter/', views.fee_collection_filter, name='fee_collection_filter'),
    path('search_student_fees/', views.search_student_fees, name='search_student_fees'),
    path('students/search', views.search_student, name='search_student'),

    path('fees/', views.fee_structure_list, name='fee_structure_list'),
    path('fees/add/', views.add_fee_structure, name='add_fee_structure'),
    path('fees/edit/<int:pk>/', views.edit_fee_structure, name='edit_fee_structure'),

    path('expenses/', views.expense_view, name='expense_view'),
    path('expenses/delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),

]
