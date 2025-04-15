from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime

class User(AbstractUser):
    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = ["email"]


class Teacher(models.Model):
    TEACHER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('principal', 'Principal'),
        ('class_teacher', 'Class Teacher'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TEACHER_TYPE_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    school = models.CharField(max_length=100)
    school_id = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

@receiver(post_save, sender=User)
def create_admin_teacher(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        Teacher.objects.get_or_create(
            user=instance,
            defaults={
                "name": "Admin",
                "type": "admin",
                "email": instance.email,
                "phone": "6395780245",
                "date_of_birth": datetime.strptime("25-11-2005", "%d-%m-%Y").date(),
                "school": "edumet",
                "address": "Onsite",
                "city": "administry",
                "state": "administration",
                "pincode": "000000",
                "school_id": "0"
            }
        )

class School(models.Model):
    name = models.CharField(max_length=100)
    school_type = models.CharField(max_length=50)
    board = models.CharField(max_length=50)
    medium = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}"