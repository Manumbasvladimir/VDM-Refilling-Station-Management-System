from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import CustomerProfileForm
from .models import CustomerProfile


@login_required
def profile(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "customers/profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def edit_profile(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = CustomerProfileForm(
            request.POST,
            instance=profile,
        )

        if form.is_valid():

            form.save()

            return redirect("customers:profile")

    else:

        form = CustomerProfileForm(
            instance=profile
        )

    return render(
        request,
        "customers/edit_profile.html",
        {
            "form": form,
        },
    )