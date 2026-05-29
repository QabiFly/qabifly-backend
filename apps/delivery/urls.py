from django.urls import path
from .views import (
    MyDeliveryProfileView,
    UpdateAvailabilityView,
    UpdateLocationView,
    MyAssignmentsView,
    ActiveAssignmentView,
    AcceptAssignmentView,
    MarkPickedView,
    VerifyAndDeliverView,
    AdminAssignDeliveryView,
    AdminAutoAssignView,
    AdminDeliveryListView,
    AdminDeliveryBoysView,
    RateDeliveryView,
)

urlpatterns = [
    # Delivery Boy
    path("profile/",                                    MyDeliveryProfileView.as_view(),  name="delivery-profile"),
    path("availability/",                               UpdateAvailabilityView.as_view(), name="delivery-availability"),
    path("location/",                                   UpdateLocationView.as_view(),     name="delivery-location"),
    path("assignments/",                                MyAssignmentsView.as_view(),      name="my-assignments"),
    path("assignments/active/",                         ActiveAssignmentView.as_view(),   name="active-assignment"),
    path("assignments/<uuid:assignment_id>/accept/",    AcceptAssignmentView.as_view(),   name="assignment-accept"),
    path("assignments/<uuid:assignment_id>/picked/",    MarkPickedView.as_view(),         name="assignment-picked"),
    path("assignments/<uuid:assignment_id>/deliver/",   VerifyAndDeliverView.as_view(),   name="assignment-deliver"),
    path("assignments/<uuid:assignment_id>/rate/",      RateDeliveryView.as_view(),       name="assignment-rate"),

    # Admin
    path("admin/assign/",                               AdminAssignDeliveryView.as_view(),  name="admin-assign"),
    path("admin/auto-assign/",                          AdminAutoAssignView.as_view(),      name="admin-auto-assign"),
    path("admin/list/",                                 AdminDeliveryListView.as_view(),    name="admin-delivery-list"),
    path("admin/boys/",                                 AdminDeliveryBoysView.as_view(),    name="admin-delivery-boys"),
]