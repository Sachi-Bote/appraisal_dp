from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HODProfile, Department


@receiver(post_save, sender=HODProfile)
def sync_hod_to_department(sender, instance, created, **kwargs):
    department = instance.department

    if department.hod != instance.user:
        department.hod = instance.user
        department.save()
