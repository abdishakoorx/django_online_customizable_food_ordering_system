# Generated by Django 4.2.1 on 2023-07-08 16:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customize', '0007_rename_customer_order_customer_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='customer_name',
            new_name='customer',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='restaurant_name',
            new_name='restaurant',
        ),
    ]