from django.urls import path

from . import views

urlpatterns = [
    path('teachers/', views.teachers, name='teachers'),
    path('add-teacher',views.add_teacher,name='add_teacher'),
    path('teachers/edit<int:id>',views.edit_teacher,name='edit_teacher'),
    path('record-marks/<int:subject_id>/<int:term_id>/', views.record_marks_view, name='record_marks'),

    path('department-asign/edit<int:teacher_id>',views.assign_department,name='assign_department'),

    path('teachers/department-asign',views.teachers_department,name='teachers_department'),

path("departments/", views.department_list, name="departments"),
path("departments/add", views.add_department, name="add_department"),


    ]