from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [

    # ======================================================
    # CUSTOMER
    # ======================================================

    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders",
    ),

    path(
        "<int:order_id>/cancel/",
        views.cancel_order,
        name="cancel_order",
    ),

    # ======================================================
    # STAFF / OWNER
    # ======================================================

    path(
        "manage/",
        views.order_list,
        name="order_list",
    ),

    path(
        "<int:order_id>/status/",
        views.update_order_status,
        name="update_order_status",
    ),

    # ======================================================
    # ORDER DETAIL
    # ======================================================

    path(
        "<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),

]