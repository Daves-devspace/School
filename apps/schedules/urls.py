from django.urls import path
from . import views

# from .views import generate_timetable_for_all

urlpatterns = [
    # subjects
    path('subjects/add/', views.add_subject, name='add_subject'),

    # rooms
    path('rooms/', views.add_room_and_list, name='add_edit_room_and_list'),  # For adding rooms
    path('rooms/edit/<int:room_id>/', views.add_room_and_list, name='edit_room'),  # For editing rooms

    # path('generate_timetable/', generate_timetable_for_all, name='generate_timetable'),
    path('generate_timetable/', views.
         generate_timetable_view, name='generate_timetable_view'),
    path('api/shuffles', views.auto_create_timetable_slots_for_all, name='generate_timetable_for_all'),
    path('timetables/', views.timetable_page_view, name='timetable_page'),
    path('timetable/', views.get_filtered_timetable, name='get_filtered_timetable'),

    path('fetch_timetable/<int:grade_section_id>/', views.fetch_timetable_by_grade_section,
         name='fetch_timetable_by_grade_section'),
]

# from django.urls import path
# from rest_framework.authtoken.views import obtain_auth_token
#
# from . import views
# from .views import create_timetable, SubjectListView, GradeSectionListView, TeacherAssignmentListView, \
#     TimetableCreateView, Pdf
#
# urlpatterns = [
#     # Teacher Assignment
#     # path('api/teachers/', views.TeacherListView.as_view(), name='teacher-list'),
#     path('api/timetable/create/', create_timetable, name='api-create-timetable'),
#     path('api/token/', obtain_auth_token, name='api_token_auth'),
#     # URL to render the template for the timetable
#     path('api/timetable/create/', TimetableCreateView.as_view(), name='timetable-create-v1'),
#     path('api/subjects/', SubjectListView.as_view(), name='subject-list'),
#     path('api/grade-sections/', GradeSectionListView.as_view(), name='grade-section-list'),
#     path('api/teachers/', TeacherAssignmentListView.as_view(), name='teacher-list'),
#     # path('api/teacher-assignment/', views.TeacherAssignmentView.as_view(), name='teacher-assignment'),  # Update here
#     # path('api/teacher-assignment/available-subjects/', views.AvailableSubjectsView.as_view(), name='available-subjects'),
#     # path('api/teacher-assignment/available-grades-sections/', views.AvailableGradeSectionsView.as_view(), name='available-grades-sections'),
#     #
#     # # Timetable
#     # path('api/timetable/student-schedule/', views.StudentTimetableView.as_view(), name='student-schedule'),
#     #
#     # # Upcoming Events
#     # path('api/events/upcoming-events/', views.UpcomingEventsView.as_view(), name='upcoming-events'),
# path('add_teachers', views.addInstructor, name='addInstructors'),
#     path('teachers_list/', views.inst_list_view , name='editinstructor'),
#     path('delete_teacher/<int:pk>/', views.delete_instructor, name='deleteinstructor'),
#
#     path('add_rooms', views.addRooms, name='addRooms'),
#     path('rooms_list/', views.room_list, name='editrooms'),
#     path('delete_room/<int:pk>/', views.delete_room, name='deleteroom'),
#
#     path('add_timings', views.addTimings, name='addTimings'),
#     path('timings_list/', views.meeting_list_view, name='editmeetingtime'),
#     path('delete_meetingtime/<str:pk>/', views.delete_meeting_time, name='deletemeetingtime'),
#
#     path('add_courses', views.addCourses, name='addCourses'),
#     path('courses_list/', views.course_list_view, name='editcourse'),
#     path('delete_course/<str:pk>/', views.delete_course, name='deletecourse'),
#
#     path('add_departments', views.addDepts, name='addDepts'),
#     path('departments_list/', views.department_list, name='editdepartment'),
#     path('delete_department/<int:pk>/', views.delete_department, name='deletedepartment'),
#
#     path('add_sections', views.addSections, name='addSections'),
#     path('sections_list/', views.section_list, name='editsection'),
#     path('delete_section/<str:pk>/', views.delete_section, name='deletesection'),
#
#     path('generate_timetable', views.generate, name='generate'),
#
#     path('timetable_generation/', views.timetable, name='timetable'),
#     path('timetable_generation/render/pdf', Pdf.as_view(), name='pdf'),
#
# ]
