from django.contrib import admin

from apps.students.models import Student, Book, Transaction, Payment, Parent, Class, Section, StudentParent

# Register your models here.
admin.site.site_header ='Merryland Management System'
admin.site.site_title = 'Merryland Friends'

class ClassAdmin(admin.ModelAdmin):
    list_display = ['name']

class SectionAdmin(admin.ModelAdmin):
    list_display = ['name','grade','class_teacher']
    search_fields = ['name','grade','class_teacher']
    list_per_page = 30



class ParentAdmin(admin.ModelAdmin):
    list_display = ['first_name','last_name','mobile']
    search_fields = ['first_name','last_name','mobile']
    list_per_page = 30


class StudentParentAdmin(admin.ModelAdmin):
    list_display = ['student','parent','relationship']
    search_fields = ['student','parent','relationship']
    list_per_page = 30


class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'Class', 'admission_number', 'gender']
    search_fields = ['first_name', 'Class', 'admission_number']
    list_per_page = 30


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'year', 'isbn', 'subject']
    search_fields = ['title', 'author', 'year', 'isbn', 'subject']
    list_per_page = 35


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'status', 'expected_return_date']
    search_fields = ['book', 'student', 'status', 'expected_return_date']
    list_per_page = 25


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'code', 'status', 'amount', 'created_at']
    search_fields = ['transaction', 'code', 'status', 'amount', 'created_at']
    list_per_page = 25


admin.site.register(Student, StudentAdmin)
admin.site.register(Parent,ParentAdmin)
admin.site.register(StudentParent,StudentParentAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Payment, PaymentAdmin)


