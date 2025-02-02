from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.timezone import now

from apps.management.models import Profile
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
    list_display = ('id_No', 'first_name','last_name', 'staff_number', 'email', 'phone', 'gender', 'is_headteacher')

    # Define search fields to enable searching by teacher's name, email, etc.
    search_fields = ['first_name','last_name', 'email', 'staff_number', 'phone']

    def save_model(self, request, obj, form, change):
        """
        Override the save_model method to handle User creation and linking staff_number as username.
        """
        # Extract email, password, and phone number from the form's cleaned data
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        phone = form.cleaned_data.get('phone')

        # Ensure phone is properly formatted
        if phone and phone.startswith('07'):
            phone = '+254' + phone[1:]  # Format Kenyan number to international format
            obj.phone = phone  # Update the Teacher's phone field with the formatted number

        if change:  # If updating an existing Teacher
            if obj.user:  # If the Teacher is already linked to a User
                user = obj.user
                user.email = email
                user.username = obj.staff_number  # Update username with the staff number
                if password:  # Update password if provided
                    user.set_password(password)
                user.save()
            else:
                # If no User is linked, create a new User
                user = User.objects.create_user(username=obj.staff_number, email=email, password=password)
                obj.user = user
        else:  # If creating a new Teacher
            # Generate staff_number if it's not yet set
            if not obj.staff_number:
                obj.staff_number = obj.generate_staff_number()

            # Create a new User using the staff_number as username
            user = User.objects.create_user(username=obj.staff_number, email=email, password=password)
            obj.user = user

        # Save the Teacher instance
        super().save_model(request, obj, form, change)

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
        if obj.staff_number:
            return obj.staff_number.split("/")[0]  # Adjust the split for format "TCH/XXX/YY"
        return 'N/A'

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