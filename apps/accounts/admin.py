from django.contrib import admin

from apps.accounts.models import FeeRecord, FeePayment, FeeStructure, Customer, Invoice, InvoiceItem, BankDetail, \
    FeeAdjustment


# Register your models here.
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['fee_record','date','amount']
    search_fields = [ 'date', 'amount']

class FeeRecordAdmin(admin.ModelAdmin):
    exclude = ('balance',)
    list_display = ['student','term','paid_amount']
    search_fields = [ 'paid_amount']

class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('grade', 'term', 'tuition_fee')
    list_filter = ('grade', 'term')
    search_fields = ('grade__name', 'term__name')


class FeeAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('fee_record','adjustment_type','amount','description')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name','phone','country')
    list_filter = ('name','phone')
    search_fields = ('name','phone')

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('customer','invoice_number','issue_date','due_date','total_amount','status')
    list_filter = ('invoice_number','issue_date','due_date','total_amount','status')
    search_fields = ('invoice_number','issue_date','due_date','status')

class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice','description','category','quantity','amount')
    list_filter = ('invoice','category','quantity','amount')
    search_fields = ('quantity','amount')

class BankDetailAdmin(admin.ModelAdmin):
    list_display = ('invoice','account_holder_name','bank_name','account_number','ifsc_code')
    list_filter = ('invoice','account_holder_name','bank_name','account_number')
    search_fields = ('invoice','account_holder_name','bank_name','account_number')



admin.site.register(FeeRecord,FeeRecordAdmin)
admin.site.register(FeeAdjustment,FeeAdjustmentAdmin)
admin.site.register(FeePayment,FeePaymentAdmin)
admin.site.register(FeeStructure,FeeStructureAdmin)
admin.site.register(Customer,CustomerAdmin)
admin.site.register(Invoice,InvoiceAdmin)
admin.site.register(InvoiceItem,InvoiceItemAdmin)
admin.site.register(BankDetail,BankDetailAdmin)

