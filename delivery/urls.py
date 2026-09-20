from django.urls import path

from . import views

app_name = "delivery"

urlpatterns = [

    # OWNER / STAFF overview
    path("", views.delivery_list, name="list"),

    # OWNER — assignment
    path("assign/", views.assign_list, name="assign_list"),
    path("assign/<int:delivery_id>/", views.assign_delivery, name="assign"),

    # STAFF — rider queue
    path("my-deliveries/", views.my_deliveries, name="my_deliveries"),

    # CUSTOMER — active deliveries
    path("my/", views.customer_deliveries, name="customer_deliveries"),

    # History / archive
    path("history/", views.delivery_history, name="history"),
    path("<int:delivery_id>/retry/", views.retry_delivery, name="retry"),

    # Shared tracking + status update
    path("<int:delivery_id>/", views.delivery_tracking, name="tracking"),
    path("<int:delivery_id>/update/", views.update_delivery_status, name="update_status"),
]