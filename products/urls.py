from django.urls import path

from . import views


app_name = "products"


urlpatterns = [

    # =========================
    # CUSTOMER
    # =========================

    path(
        "",
        views.product_list,
        name="product_list",
    ),

    path(
        "add-to-cart/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart",
    ),

    path(
        "cart/",
        views.cart,
        name="cart",
    ),

    path(
        "cart/update/<int:product_id>/",
        views.update_cart,
        name="update_cart",
    ),

    path(
        "cart/remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),


    # =========================
    # OWNER
    # =========================

    path(
        "manage/",
        views.manage_products,
        name="manage_products",
    ),

    path(
        "manage/create/",
        views.create_product,
        name="create_product",
    ),

    path(
        "manage/<int:product_id>/",
        views.detail_product,
        name="detail_product",
    ),

    path(
        "manage/<int:product_id>/update/",
        views.update_product,
        name="update_product",
    ),

    path(
        "manage/<int:product_id>/delete/",
        views.delete_product,
        name="delete_product",
    ),

]