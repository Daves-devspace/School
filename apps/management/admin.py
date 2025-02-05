from datetime import timezone

from django.contrib import admin

from django.utils.html import format_html
from django_ckeditor_5.fields import CKEditor5Field
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.management import models
from apps.management.models import Term, ReportCard, SubjectMark, ExamType, Timetable, \
    LessonExchangeRequest, Institution, Profile, HolidayPresentation, Attendance



class ProfileAdmin(admin.ModelAdmin):
    formfield_overrides = {
        CKEditor5Field: {'widget': CKEditor5Widget()},
    }


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name','mobile_number','email_address')

# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ['name']
#     search_fields = ['name','grade']



# Admin classes
class TermAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'get_year', 'start_date', 'end_date')
    list_filter = ('name',)

    # Override the queryset to order terms by the current year first
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('-start_date')  # Order by start_date in descending order

    # Custom method to display the year of the term
    def get_year(self, obj):
        return obj.year
    get_year.admin_order_field = 'start_date'  # Allow sorting by year based on start_date
    get_year.short_description = 'Year'

    # Optionally, you can set default ordering in the admin
    ordering = ['-start_date']  # Default ordering by start_date



class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'grade_assigned']
    search_fields = ['teacher__username', 'subject__name', 'grade_assigned__name']
    list_filter = ['grade_assigned']

class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    list_filter = ['name']


class SubjectMarkInline(admin.TabularInline):
    model = SubjectMark
    extra = 1
    fields = ('subject', 'marks', 'max_score', 'percentage')
    readonly_fields = ('percentage',)
    can_delete = False
    ordering = ['subject']




class SubjectMarkAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_exam_type', 'get_term', 'get_year', 'subject__name', 'marks', 'max_score', 'percentage')
    list_filter = ('report_card__term', 'report_card__exam_type', 'report_card__year', 'subject')
    search_fields = ('report_card__student__first_name', 'subject__name')

    def get_student(self, obj):
        return obj.report_card.student.first_name
    get_student.short_description = "Student"

    def get_exam_type(self, obj):
        return obj.report_card.exam_type.name if obj.report_card.exam_type else "N/A"
    get_exam_type.short_description = "Exam Type"

    def get_term(self, obj):
        return obj.report_card.term.name
    get_term.short_description = "Term"

    def get_year(self, obj):
        return obj.report_card.year
    get_year.short_description = "Year"



class ReportCardInline(admin.TabularInline):
    model = ReportCard
    extra = 1
    fields = ('term', 'exam_type', 'total_marks', 'average_marks', 'grade', 'rank', 'attendance_percentage',
              'teacher_remarks', 'conduct_remarks', 'extra_curricular_activities', 'achievements',
              'final_comments', 'parent_teacher_meeting_date', 'parent_feedback')
    readonly_fields = ('total_marks', 'average_marks', 'grade', 'rank')  # Make computed fields readonly
    can_delete = False
    ordering = ['term', 'exam_type']
    inlines = [SubjectMarkInline]  # Inline for subject marks




class ReportCardAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'term', 'exam_type', 'year', 'total_marks', 'average_marks', 'rank', 'grade', 'subject_marks')
    list_filter = ('term', 'exam_type', 'student__grade', 'year')  # Corrected filter for 'exam_type'
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')

    # Custom method to display the student's name
    def student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    student_name.admin_order_field = 'student__last_name'

    # Custom method for rank, which is calculated
    def rank(self, obj):
        return obj.student_rank()

    rank.admin_order_field = 'rank'

    # Add links to subject marks for better usability
    def subject_marks(self, obj):
        subject_marks = SubjectMark.objects.filter(report_card=obj)
        marks_details = ', '.join([f"{sm.subject.name}: {sm.marks}/{sm.max_score}" for sm in subject_marks])
        return format_html(f"<b>{marks_details}</b>") if marks_details else "No Marks"

    subject_marks.short_description = "Subject Marks"

    # Display total marks as a link
    def total_marks(self, obj):
        return obj.total_marks

    total_marks.admin_order_field = 'total_marks'

    # Display average marks as a link
    def average_marks(self, obj):
        return obj.average_marks

    average_marks.admin_order_field = 'average_marks'

    # Filter by year and grade
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        grade_filter = request.GET.get('grade')
        year_filter = request.GET.get('year')
        if grade_filter:
            queryset = queryset.filter(student__grade=grade_filter)
        if year_filter:
            queryset = queryset.filter(year=year_filter)
        return queryset












class TimetableAdmin(admin.ModelAdmin):
    list_display = ('grade_section', 'subject', 'teacher', 'day', 'start_time', 'end_time')
    list_filter = ('grade_section', 'day')
    search_fields = ('grade_section__grade__name', 'subject__name', 'teacher__full_name')


class LessonExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher_1', 'teacher_2', 'lesson_1', 'lesson_2', 'status', 'conflict', 'created_at')
    actions = ['approve_exchange', 'reject_exchange']

    def approve_exchange(self, request, queryset):
        queryset.update(status='approved')

    def reject_exchange(self, request, queryset):
        queryset.update(status='rejected')


class HolidayPresentationAdmin(admin.ModelAdmin):
    list_display = ('user_profile','title','created_at')


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'teacher', 'date', 'term', 'is_present', 'absence_reason')
    search_fields = ('student__name', 'teacher__username', 'section__grade_name', 'term__name')
    list_filter = ('term', 'section', 'is_present', 'date')
    fields = ('student', 'section', 'teacher', 'date', 'term', 'is_present', 'absence_reason')
    autocomplete_fields = ('student', 'section', 'teacher', 'term')  # Ensure teacher is correctly linked
    ordering = ('-date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('student', 'section', 'teacher', 'term')





# Register the model with the custom admin configuration


# Registering models with admin
admin.site.register(Institution,InstitutionAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(LessonExchangeRequest,LessonExchangeRequestAdmin)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(ExamType, ExamTypeAdmin)



admin.site.register(ReportCard, ReportCardAdmin)
admin.site.register(SubjectMark, SubjectMarkAdmin)
admin.site.register(HolidayPresentation,HolidayPresentationAdmin)
admin.site.register(Attendance, AttendanceAdmin)