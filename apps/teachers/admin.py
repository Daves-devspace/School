from django.contrib import admin

from apps.teachers.forms import TeacherForm
from apps.teachers.models import  Teacher, Department, TeacherAssignment, TeacherRole, Role


# Register your models here.
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ['name']
#

class TeacherRoleInline(admin.TabularInline):
    model = TeacherRole
    extra = 1  # Allow adding roles in the admin interface


class TeacherAdmin(admin.ModelAdmin):
    form = TeacherForm
    list_display = ('id_No', 'get_display_name', 'full_name', 'staff_number', 'email', 'gender', 'is_headteacher')

    # Define search fields to enable searching by teacher's name, email, etc.
    search_fields = ['full_name', 'email', 'staff_number']

    def get_form(self, request, obj=None, **kwargs):
        """
        Customize the form to prefill the staff_number when adding a new Teacher.
        """
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # When adding a new teacher
            form.base_fields['staff_number'].initial = Teacher.generate_staff_number()
        return form

    def staff_number_prefix(self, obj):
        """
        Display the prefix part of the staff_number.
        """
        return obj.staff_number.split('-')[0]  # Assuming staff number format is "TCH-XXX-YY"

    staff_number_prefix.short_description = 'Staff Number Prefix'

    def get_readonly_fields(self, request, obj=None):
        """
        Make staff_number readonly when editing an existing teacher.
        """
        if obj:  # If editing an existing object
            return ['staff_number']
        return []




class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher','grade_section','subject','assigned_date']
    list_filter = ['subject','grade_section']
    search_fields = ['teacher__full_name','subject__name','grade_section__grade__name']


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_hod')  # Display department name and current HOD (teacher)
    list_filter = ('hod',)              # Allow filtering by HOD
    search_fields = ('name',)           # Enable search by department name
    autocomplete_fields = ('hod',)      # Use autocomplete for the HOD field
    inlines = [TeacherRoleInline]       # Inline role management if needed

    def get_hod(self, obj):
        return obj.hod.full_name if obj.hod else None
    get_hod.short_description = 'Head of Department'



admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Role)
admin.site.register(TeacherRole)
admin.site.register(TeacherAssignment,TeacherAssignmentAdmin)
admin.site.register(Department,DepartmentAdmin)