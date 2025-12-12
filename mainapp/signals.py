import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Teacher

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
                "school_id": "0",
                "class_assigned": "admin_class",
                "mfa_enabled": True,
            }
        )
