from django.contrib import admin
from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "barangay",
        "municipality",
        "province",
        "gallon_balance",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
    )