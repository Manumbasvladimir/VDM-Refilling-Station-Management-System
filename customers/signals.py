from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from .models import CustomerProfile


@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Automatically create a CustomerProfile
    for every newly registered customer.
    """
    if created and instance.role == User.Role.CUSTOMER:
        CustomerProfile.objects.create(user=instance)