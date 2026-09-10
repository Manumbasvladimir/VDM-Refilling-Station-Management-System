from django.db import models


class Product(models.Model):

    class Category(models.TextChoices):
        GALLON = "GALLON", "Gallon"
        BOTTLED = "BOTTLED", "Bottled Water"
        ACCESSORY = "ACCESSORY", "Accessory"

    name = models.CharField(max_length=100)

    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(default=0)

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name