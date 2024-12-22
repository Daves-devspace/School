from django.contrib import admin

from apps.teachers.models import Subject, Teacher, Department, TeachingAssignment, TeacherRole, Role


# Register your models here.
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ['name']
#

class TeacherRoleInline(admin.TabularInline):
    model = TeacherRole
    extra = 1  # Allow adding roles in the admin interface

class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name','grade']

class TeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name','teacher_id','phone_no']
    filter_horizontal = ['subjects']# Makes selecting multiple subjects easier
    list_filter = ['role']
    search_fields = ('full_name', 'phone_no')


class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher','section','subject','assigned_on']
    list_filter = ['subject','section']
    search_fields = ['teacher__full_name','subject__name','section__name']


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'hod')  # Display the name and current HOD
    list_filter = ('hod',)         # Allow filtering by HOD
    search_fields = ('name',)      # Enable search by department name
    autocomplete_fields = ('hod',) # Use autocomplete for the HOD field if there are many teachers
    inlines = [TeacherRoleInline]  # Add inline role management

admin.site.register(Subject, SubjectAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Role)
admin.site.register(TeacherRole)
admin.site.register(TeachingAssignment,TeachingAssignmentAdmin)
admin.site.register(Department,DepartmentAdmin)