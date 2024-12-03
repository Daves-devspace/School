from django.urls import path

from . import views

urlpatterns = [
    path('teachers/', views.teachers, name='teachers'),
    path('add-teacher',views.add_teacher,name='add_teacher'),
    path('teachers/edit<int:id>',views.edit_teacher,name='edit_teacher'),


    ]