from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )
    mobile_number = models.CharField(max_length=20, blank=True)
    house_number = models.CharField(max_length=50, blank=True)
    street = models.CharField(max_length=150, blank=True)
    barangay = models.CharField(max_length=100)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10, blank=True)

    landmark = models.CharField(max_length=255, blank=True)

    delivery_notes = models.TextField(blank=True)

    gallon_balance = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} Profile"