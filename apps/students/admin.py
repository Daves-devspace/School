from django.contrib import admin
from django.db.models import F, Count
from django.utils.timezone import now  # Correct import for timezone

from apps.management.admin import ReportCardInline, SubjectMarkInline
from apps.students.models import Student, Book, Transaction, Payment, Parent, Grade, Section, StudentParent,GradeSection

# Customize admin site headers
admin.site.site_header = 'Merryland Management System'
admin.site.site_title = 'Merryland Friends'


# Promote Students Action
def promote_students_action(modeladmin, request, queryset):
    queryset.update(last_promoted=now())  # Update last promotion date
    modeladmin.message_user(request, "Selected students were promoted successfully.")
promote_students_action.short_description = "Promote selected students"


# Admin Classes
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')  # Display name and level in the list view
    search_fields = ('name',)  # Allow search by name
    list_filter = ('level',)  # Filter by level
    ordering = ['level']  # Sort by level in ascending order


# Admin for Section
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Display name in the list view
    search_fields = ('name',)  # Allow search by name
    ordering = ['name']  # Sort by name alphabetically


class GradeSectionAdmin(admin.ModelAdmin):
    list_display = ('grade', 'section', 'class_teacher', 'student_count')  # Display grade, section, teacher, and student count
    list_filter = ('grade', 'section')  # Filter by grade and section
    search_fields = ('grade__name', 'section__name', 'class_teacher__first_name', 'class_teacher__last_name')  # Search by grade, section, or teacher's name
    raw_id_fields = ('grade', 'section', 'class_teacher')  # Use raw ID fields to avoid dropdowns in large datasets
    ordering = ['grade__level', 'section__name']  # Order by grade and section name

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Annotate with the count of students in each grade-section
        return queryset.annotate(student_count=Count('students'))  # Use related_name here

    def student_count(self, obj):
        # Display the number of students in each grade-section combination
        return obj.student_count
    student_count.admin_order_field = 'student_count'  # Allow sorting by student count
    student_count.short_description = 'Number of Students'  # Display name in the admin

class ParentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'mobile']
    search_fields = ['first_name', 'last_name', 'mobile']
    list_per_page = 30


class StudentParentAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent', 'relationship']
    search_fields = ['student__first_name', 'parent__first_name', 'relationship']  # Support related field searches
    list_per_page = 30


class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'admission_number', 'grade')  # Main student fields
    search_fields = ('first_name', 'last_name', 'admission_number')
    list_filter = ('grade',)
    inlines = [ReportCardInline]


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'year', 'isbn', 'subject']
    search_fields = ['title', 'author', 'isbn', 'subject']
    list_per_page = 35


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'status', 'expected_return_date']
    search_fields = ['book__title', 'student__first_name', 'status']
    list_per_page = 25


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'code', 'status', 'amount', 'created_at']
    search_fields = ['transaction__book__title', 'code', 'status']
    list_per_page = 25


# Register Models
admin.site.register(Student, StudentAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(StudentParent, StudentParentAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(GradeSection,GradeSectionAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Payment, PaymentAdmin)
