# Generated by Django 5.2 on 2025-04-14 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0002_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/'),
        ),
    ]
