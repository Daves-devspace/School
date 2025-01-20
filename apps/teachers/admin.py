from django.contrib import admin

from apps.teachers.models import  Teacher, Department, TeacherAssignment, TeacherRole, Role


# Register your models here.
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ['name']
#

class TeacherRoleInline(admin.TabularInline):
    model = TeacherRole
    extra = 1  # Allow adding roles in the admin interface



class TeacherAdmin(admin.ModelAdmin):
    list_display = ['staff_number','full_name','teacher_id']
    filter_horizontal = ['subjects']# Makes selecting multiple subjects easier
    search_fields = ('full_name', 'staff_number')


class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher','grade_section','subject','assigned_date']
    list_filter = ['subject','grade_section']
    search_fields = ['teacher__full_name','subject__name','grade_section__grade__name']


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'hod')  # Display the name and current HOD
    list_filter = ('hod',)         # Allow filtering by HOD
    search_fields = ('name',)      # Enable search by department name
    autocomplete_fields = ('hod',) # Use autocomplete for the HOD field if there are many teachers
    inlines = [TeacherRoleInline]  # Add inline role management


admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Role)
admin.site.register(TeacherRole)
admin.site.register(TeacherAssignment,TeacherAssignmentAdmin)
admin.site.register(Department,DepartmentAdmin)