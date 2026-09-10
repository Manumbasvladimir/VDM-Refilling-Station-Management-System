from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Product


# ============================================================
# CUSTOMER
# ============================================================

@login_required
def product_list(request):

    # Only CUSTOMERS can access the shopping page
    if request.user.role != "CUSTOMER":
        return redirect("accounts:dashboard")

    products = Product.objects.filter(
        is_available=True,
        stock__gt=0
    ).order_by(
        "category",
        "name"
    )

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
        },
    )


@login_required
def add_to_cart(request, product_id):

    # IMPORTANT:
    # Only customers can add products to cart
    if request.user.role != "CUSTOMER":
        messages.error(
            request,
            "Only customers can place orders."
        )
        return redirect("accounts:dashboard")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if not product.is_available:
        messages.error(
            request,
            "This product is currently unavailable."
        )
        return redirect("products:product_list")

    if product.stock <= 0:
        messages.error(
            request,
            "This product is out of stock."
        )
        return redirect("products:product_list")

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:

        if cart[product_id] < product.stock:

            cart[product_id] += 1

        else:

            messages.warning(
                request,
                "You cannot add more than the available stock."
            )

            return redirect("products:product_list")

    else:

        cart[product_id] = 1

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} was added to your cart."
    )

    return redirect("products:product_list")


@login_required
def cart(request):

    # Only customers can access cart
    if request.user.role != "CUSTOMER":
        return redirect("accounts:dashboard")

    cart_data = request.session.get(
        "cart",
        {}
    )

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = Product.objects.filter(
            id=product_id
        ).first()

        if product is None:
            continue

        subtotal = product.price * quantity

        total += subtotal

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            }
        )

    return render(
        request,
        "products/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        },
    )


@login_required
def update_cart(request, product_id):

    if request.user.role != "CUSTOMER":
        return redirect("accounts:dashboard")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        try:
            quantity = int(
                request.POST.get(
                    "quantity",
                    1
                )
            )

        except (TypeError, ValueError):

            quantity = 1

        cart = request.session.get(
            "cart",
            {}
        )

        product_id = str(product.id)

        if quantity <= 0:

            cart.pop(
                product_id,
                None
            )

        elif quantity > product.stock:

            messages.warning(
                request,
                f"Only {product.stock} item(s) are available."
            )

        else:

            cart[product_id] = quantity

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("products:cart")


@login_required
def remove_from_cart(request, product_id):

    if request.user.role != "CUSTOMER":
        return redirect("accounts:dashboard")

    cart = request.session.get(
        "cart",
        {}
    )

    product_id = str(product_id)

    cart.pop(
        product_id,
        None
    )

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("products:cart")


# ============================================================
# OWNER / ADMIN
# ============================================================

def owner_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if (
            request.user.is_superuser
            or request.user.role == "OWNER"
        ):

            return view_func(
                request,
                *args,
                **kwargs
            )

        messages.error(
            request,
            "You do not have permission to access this page."
        )

        return redirect(
            "accounts:dashboard"
        )

    return wrapper


@owner_required
def manage_products(request):

    products = Product.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "products/manage_products.html",
        {
            "products": products,
        },
    )


@owner_required
def create_product(request):

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save()

            messages.success(
                request,
                f"{product.name} was added successfully."
            )

            return redirect(
                "products:manage_products"
            )

    else:

        form = ProductForm()

    return render(
        request,
        "products/create.html",
        {
            "form": form,
        },
    )


@owner_required
def detail_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    return render(
        request,
        "products/detail.html",
        {
            "product": product,
        },
    )


@owner_required
def update_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():

            product = form.save()

            messages.success(
                request,
                f"{product.name} was updated successfully."
            )

            return redirect(
                "products:manage_products"
            )

    else:

        form = ProductForm(
            instance=product
        )

    return render(
        request,
        "products/update.html",
        {
            "form": form,
            "product": product,
        },
    )


@owner_required
def delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product_name = product.name

        product.delete()

        messages.success(
            request,
            f"{product_name} was deleted successfully."
        )

        return redirect(
            "products:manage_products"
        )

    return render(
        request,
        "products/delete.html",
        {
            "product": product,
        },
    )