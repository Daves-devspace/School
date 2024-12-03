from django.urls import path

from . import views

urlpatterns = [
    path('', views.teachers, name='teachers'),
    path('add',views.add_teacher,name='add_teacher'),


    ]