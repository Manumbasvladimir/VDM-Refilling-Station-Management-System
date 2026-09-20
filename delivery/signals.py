from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order
from .models import Delivery


@receiver(post_save, sender=Order)
def create_delivery_for_order(sender, instance, created, **kwargs):
    """
    Automatically create a Delivery record for every new order.
    It starts as PENDING (no rider yet) and only becomes actionable
    once staff assign a rider from the Delivery > Assign screen.
    """
    if created:
        Delivery.objects.get_or_create(order=instance)