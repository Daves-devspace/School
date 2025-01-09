from django import forms
from .models import FeeStructure, Expense


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['grade', 'term', 'tuition_fee']  # Include fields for the FeeStructure model


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'description', 'amount', 'paid_to']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'datepicker','type': 'date'}),
           # 'joining_date': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
        }