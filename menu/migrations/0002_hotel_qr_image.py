# Generated by Django 5.2.2 on 2025-07-16 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='qr_image',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/'),
        ),
    ]
