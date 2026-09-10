from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def dashboard(request):

    user = request.user

    # CUSTOMER
    if user.role == "customer":
        return render(
            request,
            "dashboard/customer_dashboard.html"
        )

    # STAFF
    elif user.role == "staff":
        return render(
            request,
            "dashboard/staff_dashboard.html"
        )

    # OWNER / ADMIN
    elif user.role == "owner" or user.is_superuser:
        return render(
            request,
            "dashboard/owner_dashboard.html"
        )

    # If no valid role
    return redirect("login")