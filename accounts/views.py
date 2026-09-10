from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import CustomerRegistrationForm
from .models import User


def login_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(request, user)

            return redirect("accounts:dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )


def register_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":

        form = CustomerRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Registration successful. Please log in."
            )

            return redirect("accounts:login")

    else:

        form = CustomerRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    if request.user.role == User.Role.OWNER:

        return render(
            request,
            "dashboard/owner_dashboard.html"
        )

    if request.user.role == User.Role.STAFF:

        return render(
            request,
            "dashboard/staff_dashboard.html"
        )

    return render(
        request,
        "dashboard/customer_dashboard.html"
    )


def logout_view(request):

    logout(request)

    return redirect("accounts:login")