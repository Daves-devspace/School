from django.contrib import admin
from .models import Subject, Room, TimeSlot, TimetableSlot

# Register the Instructor model
# @admin.register(Instructor)
# class InstructorAdmin(admin.ModelAdmin):
#     list_display = ('instructor_id', 'name', 'subjects_grades')  # Display key fields in the list view
#     search_fields = ['name']  # Allow search by instructor name
#     list_filter = ('subjects_grades',)  # Filter by subjects taught by the instructor


# Register the Subject model
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'requires_special_room', 'special_room')  # Display fields in list view
    search_fields = ['name']  # Allow search by subject name
    list_filter = ('department', 'requires_special_room')  # Filter by department and room requirements


# Register the Room model
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_name', 'is_special')  # Display room name and whether it's special
    search_fields = ['room_name']  # Allow search by room name


# Register the TimeSlot model
@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'time_range')  # Display time slot range
    search_fields = ['time_range']  # Allow search by time range
    list_filter = ('start_time', 'end_time')  # Filter by start and end time


# # Register the TeacherAssignment model
# @admin.register(TeacherAssignment)
# class TeacherAssignmentAdmin(admin.ModelAdmin):
#     list_display = ('teacher', 'subject', 'grade_section', 'assigned_date')  # Display assignment details
#     search_fields = ['teacher__name', 'subject__name', 'grade_section__grade__name']  # Search by teacher, subject, or grade section
#     list_filter = ('assigned_date', 'grade_section')  # Filter by date and grade section


# Register the TimetableSlot model
@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    # Other admin settings

    def get_form(self, request, obj=None, **kwargs):
        """
        Customize the form for the TimetableSlot.
        """
        form = super().get_form(request, obj, **kwargs)

        if obj:  # If editing an existing TimetableSlot
            timetable_slot = obj
            teacher_assignment = timetable_slot.teacher_assignment

            if teacher_assignment:
                subject = teacher_assignment.subject
                # You can now access subject through teacher_assignment
                print(f"Subject for this timetable slot: {subject}")

                # You can add custom logic to prepopulate other fields based on the subject or teacher assignment

        return form
