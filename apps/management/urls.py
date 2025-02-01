from django.urls import path

from . import views
from .views import TimetableCreateAPIView, TimetableCreateView, TimetableAPIView, LessonExchangeView, swap_lessons, \
    LessonExchangeListView

urlpatterns = [
    path('edit/term/<int:id>/', views.manage_terms, name='edit_terms'),
    path('terms/', views.manage_terms, name='terms'),

    path('manage-exam-types/', views.manage_exam_types, name='manage_exam_types'),  # Add
    path('manage-exam-types/<int:id>/', views.manage_exam_types, name='edit_exam_type'),
    path('delete-exam-type/<int:id>/', views.delete_exam_type, name='delete_exam_type'),

    path('manage-users/', views.manage_users, name='manage_users'),
    path('profile/', views.user_profile, name='user_profile'),
    path('presentations/', views.presentation_list, name='presentation_list'),
    path('presentations/<int:id>/', views.presentation_detail, name='presentation_detail'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    path('send-bulk-sms/', views.send_bulk_sms_view, name='send_bulk_sms'),
    # path('send-sms/', views.messages_view, name='send_sms'),
    path("messages/", views.messages_view, name="messages"),
    path('send-sms-to-class/', views.send_sms_to_class, name='send_sms_to_class'),

    path('send-results-sms/', views.send_results_sms, name='result_sms'),

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
    # path('performance/class/', views.class_performance_view, name='class_performance_view'),

    # path("add_results/", views.add_results, name="add_results"),
    # path("results/", views.add_results_by_class, name="add_results_by_class"),

    path('results/', views.filter_results, name='filter_results'),
    path('add_results/', views.add_results_table, name='add_results_table'),
    path('view_results/', views.view_subject_results, name='view_subject_results'),
    path('management/performance-filter/', views.performance_filter_view, name='performance_filter'),

    path('view_results/<int:grade_id>/<int:term_id>/<int:exam_type_id>/', views.view_results_table,
         name='view_results_table'),
    path('view_results/<int:grade_id>/<int:term_id>/<int:exam_type_id>/<int:grade_section_id>/',
         views.view_results_table, name='view_results_table'),
    # path('view_results_section/<int:grade_section_id>/<int:term_id>/<int:exam_type_id>/',
    #      views.view_results_table_section, name='view_results_table_section'),

    # Fetch performance by Grade Section (alternative to Grade)
    # path('management/view_results/section/<int:grade_section_id>/<int:term_id>/<int:exam_type_id>/',
    #      views.view_results_table,
    #      name='view_results_table_section'),
    path('top_students/', views.top_students_view, name='top_students'),

    path('report_card/<int:student_id>/<int:term_id>/', views.report_card_view, name='report_card_view'),

    path('attendance/mark/<int:grade_section_id>/<int:term_id>/', views.mark_attendance, name='mark_attendance'),
    path('attendance/summary/<int:grade_section_id>/<int:term_id>/', views.attendance_summary,
         name='attendance_summary'),
    path('attendance/report/<int:student_id>/', views.student_attendance_report, name='student_attendance_report'),
    path('attendance/chart-data/<int:student_id>/', views.attendance_chart_data, name='attendance_chart_data'),
    path('view_report_card/<int:student_id>/<int:term_id>/<int:exam_type_id>/', views.view_report_card,
         name='view_report_card'),

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

    path('timetable/create/', TimetableCreateView.as_view(), name='timetable-create'),
    path('timetable/', views.class_timetable_view, name='class-timetable'),
    path('api/grade-sections/', views.get_grade_sections, name='get-grade-sections'),  # URL pattern for your endpoint
    path('api/timetable/create/', TimetableCreateAPIView.as_view(), name='timetable-create-api'),

    # path('timetable/', TimetableView.as_view(), name='class_timetable'),

    path('api/timetable/', TimetableAPIView.as_view(), name='timetable_api'),

    path('exchange-lessons/', LessonExchangeView.as_view(), name='exchange-lessons'),

    path('lesson-exchange-list/', LessonExchangeListView.as_view(), name='lesson-exchange-list'),
    path('swap-lessons/<int:pk>/', swap_lessons, name='swap-lessons'),

    path('api/teacher/<int:teacher_id>/schedule/<str:date_str>/', views.TeacherScheduleAPIView.as_view(),
         name='teacher_schedule_api'),

]
