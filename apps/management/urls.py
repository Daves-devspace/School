from django.urls import path

from . import views

urlpatterns = [

    path('send-bulk-sms/', views.send_bulk_sms_view, name='send_bulk_sms'),
   # path('send-sms/', views.messages_view, name='send_sms'),
    path("messages/", views.messages_view, name="messages"),
    path('send-sms-to-class/',views.send_sms_to_class, name='send_sms_to_class'),

    path('books', views.books_in_store, name='books_in_store'),
    path('borrowed/books', views.borrowed_books, name='borrowed_books'),
    path('fines', views.book_fines, name='book_fines'),
    path('issue/<int:id>', views.issue_book, name='issue_book'),
    path('return/<int:id>', views.return_book, name='return_book'),
    path('pay/<int:id>', views.pay_overdue, name='pay_overdue'),
    path('handle/paymment/transactions<int:id>', views.callback, name='callback'),
    path('performance', views.grade_performance_view, name='grade_performance_view'),
    # path("results/<int:student_id>/<int:term_id>/", views.student_results_table, name="student_results_table"),

    path('performance/<int:grade_id>/<int:term_id>/', views.grade_performance_view, name='grade_performance'),

    # URL for adding a subject
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('timetable/', views.time_table, name='time_table'),
    path('exam/', views.exam_list, name='exam_list'),
    path('transport/', views.transport_view, name='transport'),
    path('event/', views.events_view, name='event'),

    path('books/add/', views.add_book, name='add_book'),

    # URL for listing all subjects (optional, to display all subjects)
    path('subjects/', views.list_subjects, name='subjects_list'),
    path('subject_teachers/', views.subject_teachers, name='subject_teachers'),
    path('subjects_by_grade/<int:grade_id>/', views.subjects_by_grade, name='subjects_by_grade'),

    # URL for teachers to key in results for a specific subject
    # path('results/add/<int:subject_id>/', views.add_results, name='add_results'),

    # URL to view the class performance and top 5 students
    path('performance/class/', views.class_performance, name='class_performance'),
    # path("add_results/", views.add_results, name="add_results"),
    # path("results/", views.add_results_by_class, name="add_results_by_class"),

    path('results/', views.filter_results, name='filter_results'),
    path('add_results/', views.add_results_table, name='add_results_table'),
    # path('view_results/', views.view_results_table, name='view_results_table'),
    path('view_results/<int:grade_id>/<int:term_id>/<int:subject_id>/<int:exam_type_id>/', views.view_results_table,
         name='view_results_table'),

    # URL to view a single student's performance
    # path('performance/student/<int:student_id>/', views.student_performance, name='student_performance'),

    path('revenue/line-chart/', views.line_chart, name='line_chart'),

    # path('path-to-your-gender-data/', views.gender_pie_data, name='gender_pie_data'),
    path('gender-pie-chart/', views.pie_data, name='gender_pie_chart'),

    path('data-trends/', views.data_trends, name='data_trends'),
    path('trends-bar-chart-data/', views.trends_bar_chart_data, name='trends_bar_chart_data'),
    path('revenue-trend/', views.revenue_line_chart, name='revenue_line_chart'),
    path('get-students/', views.get_students_by_class, name='get_students_by_class'),

    # path('add/<int:student_id>', views.add_results, name='add_results'),
    path('view/', views.view_results, name='view_results'),
    path('filter_results/', views.filter_results, name='filter_results'),
    # path('save_results/', views.save_results, name='save_results'),

]
