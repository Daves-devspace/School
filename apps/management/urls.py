
from django.urls import path

from  .import views

urlpatterns = [

    path('books', views.books_in_store, name='books_in_store'),
    path('borrowed/books', views.borrowed_books, name='borrowed_books'),
    path('fines', views.book_fines, name='book_fines'),
    path('issue/<int:id>', views.issue_book, name='issue_book'),
    path('return/<int:id>', views.return_book, name='return_book'),
    path('pay/<int:id>',views.pay_overdue,name='pay_overdue'),
    path('handle/paymment/transactions<int:id>',views.callback,name='callback'),
    path('performance',views.grade_performance_view,name='grade_performance_view'),
    path('performance/<int:grade_id>/<int:term_id>/', views.grade_performance_view, name='grade_performance'),

    # URL for adding a subject
    path('subjects/add/', views.add_subject, name='add_subject'),

    # URL for listing all subjects (optional, to display all subjects)
     path('subjects/', views.list_subjects, name='subjects_list'),
    path('subjects_by_grade/<int:grade_id>/', views.subjects_by_grade, name='subjects_by_grade'),

    # URL for teachers to key in results for a specific subject
    path('results/add/<int:subject_id>/', views.add_results, name='add_results'),

    # URL to view the class performance and top 5 students
    path('performance/class/<int:class_id>/', views.class_performance, name='class_performance'),

    # URL to view a single student's performance
    path('performance/student/<int:student_id>/', views.student_performance, name='student_performance'),


path('revenue/line-chart/',views.line_chart, name='line_chart'),
    path('path-to-your-gender-data/', views.gender_data, name='gender_data'),

    ]