# from datetime import timezone
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from django.db import models
from django.utils.timezone import now

from apps.management.models import Term
from apps.students.models import Student


# Create your models here.
# Fee structure for each grade and term
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


# Fee record for individual students
class FeeRecord(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="fee_records")
    term = models.ForeignKey("management.Term", on_delete=models.CASCADE)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Optional fees with activation status
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_active = models.BooleanField(default=False)  # Active or not

    lunch_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lunch_active = models.BooleanField(default=False)

    remedial_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remedial_active = models.BooleanField(default=False)

    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overpayment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'term'], name='unique_fee_record_per_term')
        ]

    def save(self, *args, **kwargs):
        # Fetch previous term's fee record if it exists
        previous_term_record = FeeRecord.objects.filter(
            student=self.student,
            term=self.term.get_previous_term()  # Using get_previous_term method
        ).first()

        # Calculate previous balance
        previous_balance = previous_term_record.balance if previous_term_record else 0

        # Calculate total fee for the current term
        self.total_fee = self.calculate_total_fee() + previous_balance

        # Update balance and overpayment
        self.balance = self.total_fee - self.paid_amount
        self.overpayment = Decimal('0.0') if self.balance > Decimal('0.0') else abs(self.balance)

        super().save(*args, **kwargs)

    def calculate_total_fee(self):
        # Include only active fees (tuition is always included)
        total = self.tuition_fee
        if self.transport_active:
            total += self.transport_fee
        if self.lunch_active:
            total += self.lunch_fee
        if self.remedial_active:
            total += self.remedial_fee
        return total

    def calculate_balance(self):
        total_fee = self.calculate_total_fee()
        return total_fee - self.paid_amount

    def calculate_overpayment(self):
        balance = self.calculate_balance()
        return Decimal('0.0') if balance > Decimal('0.0') else abs(balance)

    def previous_balance(self):
        # Example logic: Fetch the balance from the last term
        previous_record = FeeRecord.objects.filter(
            student=self.student
        ).exclude(term=self.term).order_by('-term').first()
        return previous_record.calculate_balance() if previous_record else 0

    def get_previous_record(self):
        # Fetch the previous fee record for the same student based on term order
        previous_record = FeeRecord.objects.filter(
            student=self.student,
            term__start_date__lt=self.term.start_date  # Ensure correct term ordering
        ).order_by('-term__start_date').first()
        return previous_record



    def __str__(self):
        return f"{self.student.first_name} - {self.term.name} Fee Record"


# Fee adjustments for specific students
class FeeAdjustment(models.Model):
    fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="adjustments")
    adjustment_type = models.CharField(max_length=50)  # e.g., Discount, Extra Charge
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.adjustment_type} - {self.amount} for {self.fee_record}"


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

    # previous_balance = models.DecimalField(max_digits=10, decimal_places=2,
    #                                        default=0.0)
    # balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Store the balance# Keep track of previous balance
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
