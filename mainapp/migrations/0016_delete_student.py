# Generated by Django 5.2 on 2025-05-11 04:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0015_rename_contact_attendance_phone_student_phone_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Student',
        ),
    ]
