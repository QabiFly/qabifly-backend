from django.urls import path
from .views import (
    CreateTicketView,
    MyTicketsView,
    TicketDetailView,
    ReplyToTicketView,
    RateTicketView,
    AdminTicketsView,
    AdminAssignTicketView,
    AdminResolveTicketView,
)

urlpatterns = [
    path("tickets/create/",                              CreateTicketView.as_view(),        name="ticket-create"),
    path("tickets/mine/",                                MyTicketsView.as_view(),            name="my-tickets"),
    path("tickets/<str:ticket_number>/",                 TicketDetailView.as_view(),         name="ticket-detail"),
    path("tickets/<str:ticket_number>/reply/",           ReplyToTicketView.as_view(),        name="ticket-reply"),
    path("tickets/<str:ticket_number>/rate/",            RateTicketView.as_view(),           name="ticket-rate"),
    path("admin/tickets/",                               AdminTicketsView.as_view(),         name="admin-tickets"),
    path("admin/tickets/<str:ticket_number>/assign/",    AdminAssignTicketView.as_view(),    name="admin-ticket-assign"),
    path("admin/tickets/<str:ticket_number>/resolve/",   AdminResolveTicketView.as_view(),   name="admin-ticket-resolve"),
]