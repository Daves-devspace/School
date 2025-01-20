from datetime import timezone

from django.contrib import admin
from django.db.models import Sum

from apps.management.models import Term, ReportCard, SubjectMark, ExamType, Timetable, \
    LessonExchangeRequest, Subject, Institution, Profile, HolidayPresentation


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','role','phone_number')

class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name','mobile_number','email_address')

class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name','grade']

# Inline classes
class SubjectMarkInline(admin.TabularInline):
    model = SubjectMark
    extra = 1  # Number of empty rows to show for new marks
    fields = ['subject', 'marks', 'exam_type']
    readonly_fields = ['subject', 'exam_type']  # Make these fields read-only in the inline

# Admin classes
class TermAdmin(admin.ModelAdmin):
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



class SubjectMarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'marks', 'exam_type']
    list_filter = ['term', 'subject', 'exam_type']
    search_fields = ['student__first_name', 'student__last_name', 'subject__name']
    ordering = ['-marks']

# Remove SubjectMarkInline and its usage in ReportCardAdmin
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'total_marks_display', 'student_rank_display', 'date']
    search_fields = ['student__first_name', 'student__last_name', 'term__name']
    list_filter = ['term']
    ordering = ['term', '-date']

    def total_marks_display(self, obj):
        return obj.calculate_total_marks()  # Call the renamed method
    total_marks_display.short_description = 'Total Marks'

    def student_rank_display(self, obj):
        return obj.student_rank()
    student_rank_display.short_description = 'Rank'

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



# Registering models with admin
admin.site.register(Institution,InstitutionAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(LessonExchangeRequest,LessonExchangeRequestAdmin)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(ExamType, ExamTypeAdmin)

admin.site.register(Subject,SubjectAdmin)
admin.site.register(SubjectMark, SubjectMarkAdmin)
admin.site.register(ReportCard, ReportCardAdmin)
admin.site.register(HolidayPresentation,HolidayPresentationAdmin)
