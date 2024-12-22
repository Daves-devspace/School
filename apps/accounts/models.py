# from datetime import timezone
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.db import models
from django.utils.timezone import now

from apps.management.models import Term
from apps.students.models import Student,Class


# Create your models here.
class FeeStructure(models.Model):
    grade = models.ForeignKey(Class, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # due_date = models.DateField()

    def __str__(self):
        return f"{self.grade.name} - {self.term.name}:{self.amount} Fee"

class FeeRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_records')
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)  # Add the due_date field

    def balance_due(self):
        return self.total_fee - self.paid_amount

    def __str__(self):
        return f"{self.student.first_name} - {self.term.name}"

    #  override the save method to set the due date automatically
    def save(self, *args, **kwargs):
        # Automatically set the due date to the end date of the term
        if not self.due_date and self.term:
            self.due_date = self.term.end_date  # Use the end date of the term as the due date
        super(FeeRecord, self).save(*args, **kwargs)













class FeePayment(models.Model):
    fee_record = models.ForeignKey(FeeRecord, on_delete=models.CASCADE, related_name="payments")
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True)
    # previous_balance = models.DecimalField(max_digits=10, decimal_places=2,
    #                                        default=0.0)
    # balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Store the balance# Keep track of previous balance
    def __str__(self):
        return f"{self.fee_record.student} - {self.amount} on {self.date}"
    # def save(self, *args, **kwargs):
    #     # Get the previous payment's balance or use the fee record's total_fee if no previous payment
    #     if self.fee_record.payments.exists():
    #         previous_payment = self.fee_record.payments.last()
    #         self.previous_balance = previous_payment.balance  # Previous balance is the balance of the last payment
    #     else:
    #         self.previous_balance = self.fee_record.total_fee  # If no previous payment, start with total fee
    #
    #     # Calculate the new balance after the current payment
    #     balance = self.previous_balance - self.amount
    #
    #     # Save this payment's balance
    #     self.balance = max(0.0, balance)  # Ensure balance doesn't go below 0
    #
    #     # Save the FeePayment object
    #     super(FeePayment, self).save(*args, **kwargs)
    #
    #     # Update the fee record with new paid amount and balance
    #     self.fee_record.paid_amount += self.amount
    #     self.fee_record.balance = self.fee_record.total_fee - self.fee_record.paid_amount
    #     self.fee_record.save()
    #
    # def __str__(self):
    #     return f"Payment of {self.amount} for {self.fee_record.student.first_name} - Remaining Balance: {self.balance}"


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
            self.previous_balance = self.fee_record.total_fee  # If no previous installment, start with total fee

        # Calculate the balance after the current installment
        balance = self.previous_balance - self.amount
        self.balance = max(0.0, balance)  # Ensure balance doesn't go below 0

        # Save the installment
        super(Installment, self).save(*args, **kwargs)

        # Update FeeRecord with new paid_amount and balance
        self.fee_record.paid_amount += self.amount
        self.fee_record.balance = self.fee_record.total_fee - self.fee_record.paid_amount
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
    recurring_months = models.PositiveIntegerField(blank=True, null=True, help_text="Applicable for recurring invoices.")
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

