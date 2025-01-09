from django.contrib import admin
from django.db.models import Sum

from apps.management.models import Term, TeacherSubject, Result, ReportCard, SubjectMark, ExamType


# Register your models here.
class TermAdmin(admin.ModelAdmin):
    list_display = ['name','start_date','end_date']
    list_filter = ('start_date', 'end_date')
    search_fields = ['name']



class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'subject', 'grade_assigned']
    search_fields = ['teacher__username', 'subject', 'grade_assigned']

class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name','term','description']
    search_fields = ['name']

class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'teacher_subject', 'score', 'term']
    list_filter = ['term', 'teacher_subject__subject']
    search_fields = ['student__name', 'teacher_subject__subject', 'score']


class PerformanceAdmin(admin.ModelAdmin):
    list_display = ['student','subject','term','marks','total_marks']
    search_fields = ['student','subject','term','total_marks']

class SubjectMarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'marks']
    list_filter = ['term', 'subject']
    search_fields = ['student__first_name', 'subject']


class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'total_marks', 'student_rank', 'date']
    search_fields = ['student__name', 'term__name']

    def total_marks(self, obj):
        return obj.total_marks()

    def student_rank(self, obj):
        return obj.student_rank()



# admin.site.register(ReportCard, ReportCardAdmin)
admin.site.register(SubjectMark, SubjectMarkAdmin)
admin.site.register(Term,TermAdmin)
admin.site.register(ExamType,ExamTypeAdmin)

admin.site.register(TeacherSubject,TeacherSubjectAdmin)
admin.site.register(Result,ResultAdmin)
#admin.site.register(Performance,PerformanceAdmin)

