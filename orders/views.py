from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .models import Order, OrderItem


# ==========================================================
# CUSTOMER CHECKOUT
# ==========================================================

@login_required
def checkout(request):

    if request.user.role != "CUSTOMER":
        messages.error(
            request,
            "Only customers can place orders."
        )
        return redirect("accounts:dashboard")

    cart = request.session.get("cart", {})

    if not cart:
        messages.warning(
            request,
            "Your cart is empty."
        )
        return redirect("products:cart")

    cart_items = []
    total = 0

    for product_id, quantity in cart.items():

        product = get_object_or_404(
            Product,
            id=product_id
        )

        quantity = int(quantity)

        if quantity <= 0:
            continue

        if quantity > product.stock:
            messages.error(
                request,
                f"Not enough stock for {product.name}. "
                f"Only {product.stock} available."
            )
            return redirect("products:cart")

        if not product.is_available:
            messages.error(
                request,
                f"{product.name} is currently unavailable."
            )
            return redirect("products:cart")

        subtotal = product.price * quantity

        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    if not cart_items:
        messages.warning(
            request,
            "Your cart is empty."
        )
        return redirect("products:cart")

    profile = getattr(
        request.user,
        "customer_profile",
        None
    )

    if profile is None:
        messages.warning(
            request,
            "Please complete your profile before ordering."
        )
        return redirect("customers:edit_profile")

    # =========================
    # SHOW CHECKOUT
    # =========================

    if request.method == "GET":

        return render(
            request,
            "orders/checkout.html",
            {
                "cart_items": cart_items,
                "total": total,
                "profile": profile,
            },
        )

    # =========================
    # PLACE ORDER
    # =========================

    if request.method == "POST":

        delivery_notes = request.POST.get(
            "delivery_notes",
            ""
        ).strip()

        delivery_address_parts = [
            profile.house_number,
            profile.street,
            profile.barangay,
            profile.municipality,
            profile.province,
            profile.zip_code,
        ]

        delivery_address = ", ".join(
            part
            for part in delivery_address_parts
            if part
        )

        with transaction.atomic():

            # Re-check stock
            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item["product"].id
                )

                if product.stock < item["quantity"]:

                    messages.error(
                        request,
                        f"Not enough stock for {product.name}."
                    )

                    return redirect(
                        "products:cart"
                    )

                if not product.is_available:

                    messages.error(
                        request,
                        f"{product.name} is no longer available."
                    )

                    return redirect(
                        "products:cart"
                    )

            # Create order
            order = Order.objects.create(
                customer=request.user,
                total_amount=total,
                delivery_address=delivery_address,
                delivery_notes=delivery_notes,
                status=Order.Status.PENDING,
            )

            # Create order items
            for item in cart_items:

                product = Product.objects.select_for_update().get(
                    id=item["product"].id
                )

                quantity = item["quantity"]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    subtotal=product.price * quantity,
                )

                # Reduce stock
                product.stock -= quantity

                if product.stock == 0:
                    product.is_available = False

                product.save(
                    update_fields=[
                        "stock",
                        "is_available",
                    ]
                )

            # Clear cart
            request.session["cart"] = {}
            request.session.modified = True

        messages.success(
            request,
            f"Order {order.order_number} was placed successfully!"
        )

        return redirect(
            "orders:order_detail",
            order_id=order.id
        )


# ==========================================================
# ORDER DETAIL
# ==========================================================

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id
    )

    # CUSTOMER
    if request.user.role == "CUSTOMER":

        if order.customer != request.user:

            messages.error(
                request,
                "You do not have permission to view this order."
            )

            return redirect(
                "accounts:dashboard"
            )

    # STAFF / OWNER
    elif request.user.role not in ["STAFF", "OWNER"] and not request.user.is_superuser:

        messages.error(
            request,
            "You do not have permission to view this order."
        )

        return redirect(
            "accounts:dashboard"
        )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )


# ==========================================================
# STAFF / OWNER ORDER LIST
# ==========================================================

@login_required
def order_list(request):

    if request.user.role not in ["STAFF", "OWNER"] and not request.user.is_superuser:

        messages.error(
            request,
            "You do not have permission to view orders."
        )

        return redirect(
            "accounts:dashboard"
        )

    orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/order_list.html",
        {
            "orders": orders,
        },
    )


# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================

@login_required
def update_order_status(request, order_id):

    if request.user.role not in ["STAFF", "OWNER"] and not request.user.is_superuser:

        messages.error(
            request,
            "You do not have permission to update orders."
        )

        return redirect(
            "accounts:dashboard"
        )

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == "POST":

        new_status = request.POST.get(
            "status"
        )

        valid_statuses = [
            Order.Status.CONFIRMED,
            Order.Status.PREPARING,
            Order.Status.OUT_FOR_DELIVERY,
            Order.Status.DELIVERED,
            Order.Status.CANCELLED,
        ]

        if new_status not in valid_statuses:

            messages.error(
                request,
                "Invalid order status."
            )

            return redirect(
                "orders:order_list"
            )

        # Prevent changing a completed order
        if order.status == Order.Status.DELIVERED:

            messages.error(
                request,
                "A delivered order cannot be changed."
            )

            return redirect(
                "orders:order_list"
            )

        # Prevent changing a cancelled order
        if order.status == Order.Status.CANCELLED:

            messages.error(
                request,
                "A cancelled order cannot be changed."
            )

            return redirect(
                "orders:order_list"
            )

        order.status = new_status

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Order {order.order_number} is now "
            f"{order.get_status_display()}."
        )

    return redirect(
        "orders:order_list"
    )
# ==========================================================
# CUSTOMER - MY ORDERS
# ==========================================================

@login_required
def my_orders(request):

    # Only customers can access their own orders
    if request.user.role != "CUSTOMER":

        messages.error(
            request,
            "You do not have permission to view this page."
        )

        return redirect(
            "accounts:dashboard"
        )

    orders = (
        Order.objects
        .filter(customer=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/my_orders.html",
        {
            "orders": orders,
        },
    )
# ==========================================================
# CUSTOMER - CANCEL ORDER
# ==========================================================

@login_required
def cancel_order(request, order_id):

    # Only customers can cancel their orders
    if request.user.role != "CUSTOMER":

        messages.error(
            request,
            "Only customers can cancel orders."
        )

        return redirect(
            "accounts:dashboard"
        )

    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user,
    )

    # Only pending orders can be cancelled
    if order.status != Order.Status.PENDING:

        messages.error(
            request,
            "Only pending orders can be cancelled."
        )

        return redirect(
            "orders:my_orders"
        )

    if request.method == "POST":

        with transaction.atomic():

            # Lock the order to prevent duplicate cancellation
            order = (
                Order.objects
                .select_for_update()
                .get(id=order.id)
            )

            # Check again after locking
            if order.status != Order.Status.PENDING:

                messages.error(
                    request,
                    "This order can no longer be cancelled."
                )

                return redirect(
                    "orders:my_orders"
                )

            # Return products to stock
            for item in order.items.select_related("product"):

                product = item.product

                product.stock += item.quantity

                product.is_available = True

                product.save(
                    update_fields=[
                        "stock",
                        "is_available",
                    ]
                )

            # Cancel the order
            order.status = Order.Status.CANCELLED

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        messages.success(
            request,
            f"Order {order.order_number} has been cancelled."
        )

    return redirect(
        "orders:my_orders"
    )