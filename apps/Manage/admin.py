
from django.contrib import admin
from .models import SmsProviderToken



# Register your models here.



@admin.register(SmsProviderToken)
class SmsProviderTokenAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'api_token')


