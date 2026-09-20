from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from orders.models import Order

from .forms import AssignRiderForm
from .models import Delivery


# ============================================================
# ROLE HELPERS
# ============================================================

def owner_or_staff(user):
    return user.is_superuser or user.role in ("OWNER", "STAFF")


def owner_only(user):
    return user.is_superuser or user.role == "OWNER"


# ============================================================
# OWNER / STAFF — OVERVIEW OF ALL ACTIVE DELIVERIES
# ============================================================

@login_required
def delivery_list(request):

    if not owner_or_staff(request.user):
        messages.error(request, "You do not have permission to view deliveries.")
        return redirect("accounts:dashboard")

    deliveries = (
        Delivery.objects
        .select_related("order", "order__customer", "rider")
        .filter(status__in=[
            Delivery.Status.PENDING,
            Delivery.Status.ASSIGNED,
            Delivery.Status.OUT_FOR_DELIVERY,
        ])
        .order_by("status", "-created_at")
    )

    pending_count = deliveries.filter(status=Delivery.Status.PENDING).count()

    return render(
        request,
        "delivery/list.html",
        {
            "deliveries": deliveries,
            "pending_count": pending_count,
        },
    )


# ============================================================
# OWNER — ASSIGN A RIDER TO A READY ORDER
# ============================================================

@login_required
def assign_list(request):

    if not owner_only(request.user):
        messages.error(request, "Only the owner can assign deliveries.")
        return redirect("accounts:dashboard")

    # Only orders that are packed and ready (PREPARING) and not yet assigned
    ready_deliveries = (
        Delivery.objects
        .select_related("order", "order__customer")
        .filter(
            status=Delivery.Status.PENDING,
            order__status=Order.Status.PREPARING,
        )
        .order_by("created_at")
    )

    return render(
        request,
        "delivery/assign.html",
        {
            "deliveries": ready_deliveries,
            "form": AssignRiderForm(),
        },
    )


@login_required
def assign_delivery(request, delivery_id):

    if not owner_only(request.user):
        messages.error(request, "Only the owner can assign deliveries.")
        return redirect("accounts:dashboard")

    delivery = get_object_or_404(
        Delivery,
        id=delivery_id,
        status=Delivery.Status.PENDING,
    )

    if delivery.order.status != Order.Status.PREPARING:
        messages.error(
            request,
            "This order is not ready for delivery assignment yet.",
        )
        return redirect("delivery:assign_list")

    if request.method == "POST":

        form = AssignRiderForm(request.POST, instance=delivery)

        if form.is_valid():

            delivery = form.save(commit=False)
            delivery.status = Delivery.Status.ASSIGNED
            delivery.assigned_at = timezone.now()
            delivery.save()

            messages.success(
                request,
                f"{delivery.rider.get_full_name() or delivery.rider.username} "
                f"was assigned to order {delivery.order.order_number}.",
            )

            return redirect("delivery:assign_list")

        messages.error(request, "Please select a valid rider.")

    return redirect("delivery:assign_list")


# ============================================================
# STAFF — MY DELIVERY QUEUE (assigned to this rider)
# ============================================================

@login_required
def my_deliveries(request):

    if not (request.user.role == "STAFF" or request.user.is_superuser):
        messages.error(request, "You do not have permission to view this page.")
        return redirect("accounts:dashboard")

    deliveries = (
        Delivery.objects
        .select_related("order", "order__customer")
        .filter(
            rider=request.user,
            status__in=[
                Delivery.Status.ASSIGNED,
                Delivery.Status.OUT_FOR_DELIVERY,
            ],
        )
        .order_by("status", "-assigned_at")
    )

    return render(
        request,
        "delivery/my_deliveries.html",
        {
            "deliveries": deliveries,
        },
    )


# ============================================================
# CUSTOMER — MY ACTIVE DELIVERIES
# ============================================================

@login_required
def customer_deliveries(request):

    if request.user.role != "CUSTOMER":
        messages.error(request, "You do not have permission to view this page.")
        return redirect("accounts:dashboard")

    deliveries = (
        Delivery.objects
        .select_related("order", "rider")
        .filter(
            order__customer=request.user,
            status__in=[
                Delivery.Status.ASSIGNED,
                Delivery.Status.OUT_FOR_DELIVERY,
            ],
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "delivery/customer_deliveries.html",
        {
            "deliveries": deliveries,
        },
    )


# ============================================================
# TRACKING (shared detail page — customer / rider / owner)
# ============================================================

@login_required
def delivery_tracking(request, delivery_id):

    delivery = get_object_or_404(
        Delivery.objects.select_related("order", "order__customer", "rider"),
        id=delivery_id,
    )

    user = request.user

    is_owner_or_admin = owner_only(user)
    is_assigned_rider = delivery.rider_id == user.id
    is_order_owner = delivery.order.customer_id == user.id

    if not (is_owner_or_admin or is_assigned_rider or is_order_owner):
        messages.error(request, "You do not have permission to view this delivery.")
        return redirect("accounts:dashboard")

    can_update_status = is_owner_or_admin or is_assigned_rider

    return render(
        request,
        "delivery/tracking.html",
        {
            "delivery": delivery,
            "can_update_status": can_update_status,
        },
    )


# ============================================================
# RIDER / OWNER — ADVANCE DELIVERY STATUS
# ============================================================

@login_required
def update_delivery_status(request, delivery_id):

    delivery = get_object_or_404(
        Delivery.objects.select_related("order"),
        id=delivery_id,
    )

    user = request.user
    can_update = owner_only(user) or delivery.rider_id == user.id

    if not can_update:
        messages.error(request, "You do not have permission to update this delivery.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("delivery:tracking", delivery_id=delivery.id)

    action = request.POST.get("action")
    order = delivery.order

    if action == "start" and delivery.status == Delivery.Status.ASSIGNED:

        delivery.status = Delivery.Status.OUT_FOR_DELIVERY
        delivery.out_for_delivery_at = timezone.now()
        delivery.save(update_fields=["status", "out_for_delivery_at", "updated_at"])

        order.status = Order.Status.OUT_FOR_DELIVERY
        order.save(update_fields=["status", "updated_at"])

        messages.success(request, f"Order {order.order_number} is now out for delivery.")

    elif action == "delivered" and delivery.status == Delivery.Status.OUT_FOR_DELIVERY:

        delivery.status = Delivery.Status.DELIVERED
        delivery.delivered_at = timezone.now()
        delivery.notes = request.POST.get("notes", delivery.notes).strip()
        delivery.save(update_fields=["status", "delivered_at", "notes", "updated_at"])

        order.status = Order.Status.DELIVERED
        order.save(update_fields=["status", "updated_at"])

        messages.success(request, f"Order {order.order_number} marked as delivered.")

    elif action == "failed" and delivery.status == Delivery.Status.OUT_FOR_DELIVERY:

        reason = request.POST.get("notes", "").strip()

        delivery.status = Delivery.Status.FAILED
        delivery.notes = reason
        delivery.save(update_fields=["status", "notes", "updated_at"])

        order.status = Order.Status.PREPARING
        order.save(update_fields=["status", "updated_at"])

        messages.warning(
            request,
            f"Delivery for order {order.order_number} was marked as failed. "
            f"It can be reassigned from the Delivery > Assign screen.",
        )

    else:

        messages.error(request, "Invalid or out-of-sequence delivery action.")

    return redirect("delivery:tracking", delivery_id=delivery.id)


# ============================================================
# OWNER — RETRY A FAILED DELIVERY (reset for reassignment)
# ============================================================

@login_required
def retry_delivery(request, delivery_id):

    if not owner_only(request.user):
        messages.error(request, "Only the owner can retry a delivery.")
        return redirect("accounts:dashboard")

    delivery = get_object_or_404(
        Delivery,
        id=delivery_id,
        status=Delivery.Status.FAILED,
    )

    if request.method == "POST":

        delivery.status = Delivery.Status.PENDING
        delivery.rider = None
        delivery.assigned_at = None
        delivery.out_for_delivery_at = None
        delivery.save(update_fields=[
            "status", "rider", "assigned_at", "out_for_delivery_at", "updated_at",
        ])

        messages.success(
            request,
            f"Delivery for order {delivery.order.order_number} was reset for reassignment.",
        )

    return redirect("delivery:history")


# ============================================================
# OWNER / STAFF — HISTORY (completed + failed)
# ============================================================

@login_required
def delivery_history(request):

    if not owner_or_staff(request.user):
        messages.error(request, "You do not have permission to view this page.")
        return redirect("accounts:dashboard")

    deliveries = (
        Delivery.objects
        .select_related("order", "order__customer", "rider")
        .filter(status__in=[Delivery.Status.DELIVERED, Delivery.Status.FAILED])
        .order_by("-updated_at")
    )

    return render(
        request,
        "delivery/history.html",
        {
            "deliveries": deliveries,
        },
    )