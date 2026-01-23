from django.urls import path
from . import views

app_name = "customer_service"

urlpatterns = [
    path("", views.home, name="home"),
    path("chat/", views.customer_chat, name="chat"),
    path("close/<int:msg_id>/", views.close_ticket, name="close_ticket"),
]
