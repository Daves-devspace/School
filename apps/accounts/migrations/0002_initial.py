# Generated by Django 5.1.5 on 2025-01-19 15:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('management', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feerecord',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_records', to='students.student'),
        ),
        migrations.AddField(
            model_name='feerecord',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.term'),
        ),
        migrations.AddField(
            model_name='feepayment',
            name='fee_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.feerecord'),
        ),
        migrations.AddField(
            model_name='feeadjustment',
            name='fee_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='accounts.feerecord'),
        ),
        migrations.AddField(
            model_name='feestructure',
            name='grade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students.grade'),
        ),
        migrations.AddField(
            model_name='feestructure',
            name='term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='management.term'),
        ),
        migrations.AddField(
            model_name='installment',
            name='fee_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='installments', to='accounts.feerecord'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='accounts.customer'),
        ),
        migrations.AddField(
            model_name='bankdetail',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bank_details', to='accounts.invoice'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='accounts.invoice'),
        ),
        migrations.AddField(
            model_name='payment',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='accounts.invoice'),
        ),
        migrations.AddConstraint(
            model_name='feerecord',
            constraint=models.UniqueConstraint(fields=('student', 'term'), name='unique_fee_record_per_term'),
        ),
    ]
