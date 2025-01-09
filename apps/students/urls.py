from django.conf.urls.static import static
from django.urls import path

from School import settings
from . import views

urlpatterns = [
    path('', views.students, name='students'),
    path('active/', views.active_students, name='active_students'),
    path('students/update-status/', views.update_student_status, name='update_student_status'),
    path('students/reverse-status/', views.reverse_student_status, name='reverse_student_status'),

    path('promote-students/', views.promote_students_view, name='promote_students'),

    path('students/', views.students_grid, name='students_grid'),
    path('add', views.add_student, name='add_student'),
    path('detail<int:id>', views.student_details, name='student_details'),

    path('edit<int:id>', views.edit_student, name='edit_student'),

    path('delete<int:id>', views.delete_student, name='delete_student'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
