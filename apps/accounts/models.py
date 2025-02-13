# from datetime import timezone
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from django.db import models
from django.utils.timezone import now

from apps.management.models import Term
from apps.students.models import Student


# Create your models here.
# Fee structure for each grade and term


# #fee record
# class FeeRecord(models.Model):
#     student = models.ForeignKey(
#         "students.Student", on_delete=models.CASCADE, related_name="fee_records"
#     )
#     term = models.ForeignKey("management.Term", on_delete=models.CASCADE)
#     tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#
#     # Optional fees with activation status
#     transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     transport_active = models.BooleanField(default=False)
#
#     lunch_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     lunch_active = models.BooleanField(default=False)
#
#     remedial_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     remedial_active = models.BooleanField(default=False)
#
#     total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     overpayment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     due_date = models.DateField(null=True, blank=True)
#
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["student", "term"], name="unique_fee_record_per_term"
#             )
#         ]
#
#     def save(self, *args, **kwargs):
#         """
#         Override the save method to recalculate total fees, balance, and overpayment.
#         This includes updating the balance with the previous term's balance.
#         """
#         # Fetch previous balance and adjust if necessary
#         previous_balance = self.fetch_previous_balance()
#
#         # Add the previous balance to the current balance (carry-over)
#         self.balance += previous_balance
#
#         # Apply fee statuses, calculate total fee, and update balance and overpayment
#         self.apply_fee_statuses()
#         self.total_fee = self.calculate_total_fee()
#         self.update_balance_and_overpayment()
#
#         super().save(*args, **kwargs)
#
#     def fetch_previous_balance(self):
#         """
#         Fetches the previous term's balance for this student.
#         """
#         try:
#             # Fetch the previous term for this student (assuming there is a method to get previous term)
#             previous_term = self.term.get_previous_term()
#
#             # Find the fee record for the previous term
#             previous_fee_record = FeeRecord.objects.get(student=self.student, term=previous_term)
#
#             # Return the balance of the previous term
#             print(
#                 f"Fetched previous balance: {previous_fee_record.balance} for student {self.student} in term {previous_term}")
#             return previous_fee_record.balance
#
#         except FeeRecord.DoesNotExist:
#             print(f"No previous fee record found for student {self.student} in term {self.term}")
#             return Decimal("0.0")
#
#     def apply_fee_statuses(self):
#         """
#         Ensures optional fees are applied or reset based on their activation statuses.
#         """
#         if self.transport_active and not self.transport_fee:
#             self.transport_fee = self.get_fee_from_structure('transport_fee')
#
#         if self.lunch_active and not self.lunch_fee:
#             self.lunch_fee = self.get_fee_from_structure('lunch_fee')
#
#         if self.remedial_active and not self.remedial_fee:
#             self.remedial_fee = self.get_fee_from_structure('remedial_fee')
#
#     def get_fee_from_structure(self, fee_type):
#         """
#         Fetches the fee from the FeeStructure model if available.
#         """
#         try:
#             fee_structure = FeeStructure.objects.get(
#                 grade=self.student.grade.grade,
#                 term=self.term
#             )
#             return getattr(fee_structure, fee_type, Decimal("0.0"))
#         except FeeStructure.DoesNotExist:
#             return Decimal("0.0")
#
#     def calculate_total_fee(self):
#         """
#         Calculates the total fee by adding tuition and activated optional fees.
#         """
#         optional_fees = (
#             self.transport_fee if self.transport_active else Decimal("0.0"),
#             self.lunch_fee if self.lunch_active else Decimal("0.0"),
#             self.remedial_fee if self.remedial_active else Decimal("0.0"),
#         )
#         return self.tuition_fee + sum(optional_fees)
#
#     def update_balance_and_overpayment(self):
#         """
#         Calculates and updates the balance and overpayment based on paid amounts.
#         """
#         self.balance = max(self.total_fee - self.paid_amount, Decimal("0.0"))
#         self.overpayment = max(self.paid_amount - self.total_fee, Decimal("0.0"))
#
#     def __str__(self):
#         return f"FeeRecord for {self.student} (Term: {self.term})"


class FeeStructure(models.Model):
    grade = models.ForeignKey('students.Grade', on_delete=models.CASCADE)
    term = models.ForeignKey("management.Term", on_delete=models.CASCADE)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remedial_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.grade.name} - {self.term.name} Fee Structure"

    def get_total_fee(self):
        return self.tuition_fee + self.transport_fee + self.lunch_fee + self.remedial_fee





    # def apply_fee_statuses(self):
    #     if self.transport_active:
    #         self.transport_fee = self.get_fee_from_structure('transport_fee')
    #     else:
    #         self.transport_fee = Decimal("0.0")
    #
    #     if self.lunch_active:
    #         self.lunch_fee = self.get_fee_from_structure('lunch_fee')
    #     else:
    #         self.lunch_fee = Decimal("0.0")
    #
    #     if self.remedial_active:
    #         self.remedial_fee = self.get_fee_from_structure('remedial_fee')
    #     else:
    #         self.remedial_fee = Decimal("0.0")




class FeeRecord(models.Model):
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="fee_records"
    )
    term = models.ForeignKey("management.Term", on_delete=models.CASCADE)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Optional fees with activation status
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_active = models.BooleanField(default=False)

    lunch_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_active = models.BooleanField(default=False)

    remedial_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remedial_active = models.BooleanField(default=False)

    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    previous_term_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    previous_term_overpayment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overpayment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "term"], name="unique_fee_record_per_term"
            )
        ]

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure previous term balances are carried forward
        and the total fees, balances, and overpayments are correctly calculated.
        """
        self.apply_fee_statuses()

        # Fetch previous term balance and overpayment **before calculating total fees**
        previous_balance, previous_overpayment = self.get_previous_term_balance_and_overpayment()

        self.previous_term_balance = previous_balance
        self.previous_term_overpayment = previous_overpayment

        # Recalculate total fee using previous term balance/overpayment
        self.total_fee = self.calculate_total_fee()

        # Recalculate balance and overpayment
        self.update_balance_and_overpayment()

        super().save(*args, **kwargs)

    def apply_fee_statuses(self):
        """ Ensure optional fees are applied or reset based on their activation statuses. """
        if self.transport_active and not self.transport_fee:
            self.transport_fee = self.get_fee_from_structure('transport_fee')

        if self.lunch_active and not self.lunch_fee:
            self.lunch_fee = self.get_fee_from_structure('lunch_fee')

        if self.remedial_active and not self.remedial_fee:
            self.remedial_fee = self.get_fee_from_structure('remedial_fee')

    def get_fee_from_structure(self, fee_type):
        """ Fetch the fee from the FeeStructure model if available. """
        try:
            fee_structure = FeeStructure.objects.get(
                grade=self.student.grade.grade,
                term=self.term
            )
            return getattr(fee_structure, fee_type, Decimal("0.0"))
        except FeeStructure.DoesNotExist:
            return Decimal("0.0")

    def calculate_total_fee(self):
        """
        Calculate the total fee by adding tuition, activated optional fees,
        and adjusting for the previous term's balance/overpayment.
        """
        optional_fees = (
            self.transport_fee if self.transport_active else Decimal("0.0"),
            self.lunch_fee if self.lunch_active else Decimal("0.0"),
            self.remedial_fee if self.remedial_active else Decimal("0.0"),
        )

        # Add previous term balance (if any) and subtract previous term overpayment (if any)
        total_fee = self.tuition_fee + sum(optional_fees) + self.previous_term_balance - self.previous_term_overpayment

        return total_fee

    def update_balance_and_overpayment(self):
        """
        Calculate and update the balance and overpayment based on paid amounts.
        """
        self.balance = max(self.total_fee - self.paid_amount, Decimal("0.0"))
        self.overpayment = max(self.paid_amount - self.total_fee, Decimal("0.0"))

    def get_previous_term_balance_and_overpayment(self):
        """
        Fetch the previous term's balance and overpayment, ensuring that if no record exists,
        the values default to 0.0.
        """
        previous_term = self.term.get_previous_term()
        if previous_term:
            try:
                previous_fee_record = FeeRecord.objects.get(student=self.student, term=previous_term)
                return previous_fee_record.balance, previous_fee_record.overpayment
            except FeeRecord.DoesNotExist:
                return Decimal("0.0"), Decimal("0.0")
        return Decimal("0.0"), Decimal("0.0")

    def __str__(self):
        return f"FeeRecord for {self.student} (Term: {self.term})"


class FeeAdjustment(models.Model):
    DISCOUNT = 'Discount'
    EXTRA_CHARGE = 'Extra Charge'
    ADJUSTMENT_TYPES = [
        (DISCOUNT, 'Discount'),
        (EXTRA_CHARGE, 'Extra Charge'),
    ]

    FEE_TYPES = [
        ('tuition_fee', 'Tuition Fee'),
        ('transport_fee', 'Transport Fee'),
        ('lunch_fee', 'Lunch Fee'),
        ('remedial_fee', 'Remedial Fee'),
    ]

    fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="adjustments")
    adjustment_type = models.CharField(max_length=50, choices=ADJUSTMENT_TYPES)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        fee_record = self.fee_record
        adjustment_amount = self.amount

        # Ensure discounts or extra charges are only applied to active fees
        if self.fee_type in ['transport_fee', 'lunch_fee', 'remedial_fee']:
            if not getattr(fee_record, f"{self.fee_type.replace('_fee', '')}_active"):
                raise ValueError(f"{self.fee_type} is not active for this student. Activate the service first.")

        # Restrict extra charges for tuition fees
        if self.fee_type == 'tuition_fee' and self.adjustment_type == self.EXTRA_CHARGE:
            raise ValueError("Extra charges cannot be applied to tuition fees.")

        # Determine adjustment type (Discount or Extra Charge)
        if self.adjustment_type == self.DISCOUNT:
            adjustment_amount = -abs(self.amount)
        elif self.adjustment_type == self.EXTRA_CHARGE:
            adjustment_amount = abs(self.amount)

        # Update the specific fee type
        setattr(fee_record, self.fee_type, getattr(fee_record, self.fee_type) + adjustment_amount)

        # Recalculate total fee, balance, and overpayment
        fee_record.total_fee = fee_record.calculate_total_fee()
        fee_record.balance = fee_record.total_fee - fee_record.paid_amount
        fee_record.overpayment = Decimal('0.0') if fee_record.balance > Decimal('0.0') else abs(fee_record.balance)

        # Save the updated FeeRecord
        fee_record.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adjustment_type} ({self.fee_type})"




# Payment records for individual students
# class PaymentRecord(models.Model):
#     fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="payments")
#     payment_date = models.DateField()
#     amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_method = models.CharField(max_length=50, null=True, blank=True)  # e.g., Cash, M-Pesa
#     payment_reference = models.CharField(max_length=100, null=True, blank=True)
#
#     def __str__(self):
#         return f"Payment of {self.amount_paid} on {self.payment_date}"

# Override the save method to set the due date automatically and apply credit balance to reduce total fee


class FeePayment(models.Model):
    fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="payments")
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # e.g., Cash, M-Pesa
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.fee_record.student} - {self.amount} on {self.date}"


class Installment(models.Model):
    fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Balance after each installment

    def save(self, *args, **kwargs):
        # Get the previous installment's balance, if exists
        if self.fee_record.installments.exists():
            previous_installment = self.fee_record.installments.last()
            self.previous_balance = previous_installment.balance
        else:
            self.previous_balance = self.fee_record.calculate_total_fee()  # If no previous installment, start with total fee

        # Calculate the balance after the current installment
        balance = self.previous_balance - self.amount
        self.balance = max(0.0, balance)  # Ensure balance doesn't go below 0

        # Save the installment
        super(Installment, self).save(*args, **kwargs)

        # Update FeeRecord with new paid_amount and balance
        self.fee_record.paid_amount += self.amount
        self.fee_record.balance = self.fee_record.calculate_total_fee() - self.fee_record.paid_amount
        self.fee_record.save()

    def __str__(self):
        return f"Installment of {self.amount} - Remaining Balance: {self.balance}"


class Expense(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_to = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.description} - {self.amount} paid to {self.paid_to} on {self.date}"


# Customer Information
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Invoice Model
class Invoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    recurring_months = models.PositiveIntegerField(blank=True, null=True,
                                                   help_text="Applicable for recurring invoices.")
    po_number = models.CharField(max_length=100, blank=True, null=True)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('DUE', 'Due'),
        ('OVERDUE', 'Overdue'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DUE')

    def calculate_totals(self):
        items = self.items.all()
        self.taxable_amount = sum(item.amount for item in items)
        self.total_amount = self.taxable_amount + self.additional_charges - self.discount
        self.save()

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{now().strftime('%Y%m%d')}-{self.pk or ''}"
        super().save(*args, **kwargs)
        self.calculate_totals()

    def remaining_balance(self):
        total_paid = sum(payment.amount for payment in self.payments.all())
        return self.total_amount - total_paid

    def clean(self):
        # Ensure both dates are not None
        if self.due_date and self.issue_date:
            if self.due_date < self.issue_date:
                raise ValidationError("Due date cannot be earlier than the issue date.")
        else:
            raise ValidationError("Both due date and issue date must be provided.")

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"


# Invoice Items
class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.amount = (self.price_per_item * self.quantity) * ((100 - self.discount_percentage) / 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} (Invoice {self.invoice.invoice_number})"


# Bank Details (Optional)
class BankDetail(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="bank_details")
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.bank_name} - {self.account_holder_name}"


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_number}"
