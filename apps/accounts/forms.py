from decimal import Decimal

from django import forms
from .models import FeeStructure, Expense, FeeAdjustment, FeeRecord


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


class FeeAdjustmentForm(forms.Form):
    FEE_CHOICES = [
        ("transport_fee", "Transport Fee"),
        ("lunch_fee", "Lunch Fee"),
        ("remedial_fee", "Remedial Fee"),
    ]
    ADJUSTMENT_CHOICES = [
        ("add", "Add"),
        ("subtract", "Subtract"),
    ]

    fee_type = forms.ChoiceField(choices=FEE_CHOICES, label="Fee Type")
    adjustment_type = forms.ChoiceField(choices=ADJUSTMENT_CHOICES, label="Adjustment Type")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Amount")
    description = forms.CharField(widget=forms.Textarea, label="Description", required=False)

#
# class FeeAdjustmentForm(forms.ModelForm):
#     class Meta:
#         model = FeeAdjustment
#         fields = ['fee_record', 'adjustment_type', 'fee_type', 'amount', 'description']
#
#     def __init__(self, *args, **kwargs):
#         super(FeeAdjustmentForm, self).__init__(*args, **kwargs)
#         self.fields['fee_record'].queryset = FeeRecord.objects.all()  # Filter fee records for the student
#         self.fields['amount'].initial = Decimal('0.00')  # Set initial value for the amount field to 0
#
#     def clean_amount(self):
#         amount = self.cleaned_data['amount']
#         if amount <= 0:
#             raise forms.ValidationError("The amount should be a positive value.")
#         return amount