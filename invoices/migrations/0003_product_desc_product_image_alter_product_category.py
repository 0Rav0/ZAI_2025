# Generated by Django 5.2 on 2025-05-13 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_remove_invoice_issued_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='desc',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='produkty/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('ELEC', 'Elektronika'), ('BOOK', 'Książki'), ('FOOD', 'Jedzenie'), ('OTHR', 'Inne')], default='OTHR', max_length=4),
        ),
    ]
