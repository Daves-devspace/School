from django.urls import path

from . import views

urlpatterns = [
    path('teachers/', views.teachers, name='teachers'),
    path('add-teacher', views.add_teacher, name='add_teacher'),
    path('add-teacher-assignment/', views.add_teacher_assignments, name='add_teacher_assignment'),
    path('teacher-assignments/', views.teacher_assignments_list, name='teacher_assignments'),
path('teacher-assignments/edit/<int:pk>/', views.edit_teacher_assignment, name='edit_teacher_assignment'),

    path('teachers/edit<int:id>', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:id>/', views.teacher_detail, name='teacher_detail'),  # URL pattern for teacher details
    # path('record-marks/<int:subject_id>/<int:term_id>/', views.record_marks_view, name='record_marks'),

    path('department-asign/edit<int:id>', views.assign_hod_and_teachers, name='assign_hod_and_teachers'),
    path('department-asign/add/<int:department_id>', views.assign_teachers_to_department,
         name='assign_teachers_to_department'),
    path('department/<int:department_id>/remove/<int:teacher_id>/', views.remove_teacher_from_department,
         name='remove_teacher_from_department'),

    path('teachers/department-asign', views.teachers_department, name='teachers_department'),
    path('teachers/class-teachers', views.class_teachers, name='class_teachers'),

    path('teachers/<int:teacher_id>/assign-class/', views.assign_grade, name='assign_class'),

    path("departments/", views.department_list, name="departments"),
    path("departments/add", views.add_department, name="add_department"),

]
