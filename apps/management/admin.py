from django.contrib import admin
from django.db.models import Sum

from apps.management.models import Term, Result, ReportCard, SubjectMark, ExamType, Timetable, \
    LessonExchangeRequest, UserProfile, Subject, Institution


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user','role')

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
    list_display = ['name', 'start_date', 'end_date']
    list_filter = ('start_date', 'end_date')
    search_fields = ['name']
    ordering = ['start_date']

class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'grade_assigned']
    search_fields = ['teacher__username', 'subject__name', 'grade_assigned__name']
    list_filter = ['grade_assigned']

class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'term', 'description']
    search_fields = ['name']
    list_filter = ['term']

class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'score', 'term']
    list_filter = ['term', 'subject']
    search_fields = ['student__first_name', 'student__last_name', 'teacher_subject__name', 'score']
    ordering = ['-score']

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



# Registering models with admin
admin.site.register(Institution,InstitutionAdmin)
admin.site.register(UserProfile,UserProfileAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(LessonExchangeRequest,LessonExchangeRequestAdmin)
admin.site.register(Timetable, TimetableAdmin)
admin.site.register(ExamType, ExamTypeAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Subject,SubjectAdmin)
admin.site.register(SubjectMark, SubjectMarkAdmin)
admin.site.register(ReportCard, ReportCardAdmin)
