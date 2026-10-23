"""urls.py - /payments/ URLs."""
from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("", views.payment_list, name="payment_list"),
    path("pay/", views.upload, name="upload"),
    path("<int:pk>/", views.payment_detail, name="payment_detail"),
    path("<int:pk>/payslip/", views.payslip, name="payslip"),
    path("<int:pk>/review/", views.review, name="review"),
    path("<int:pk>/receipt.pdf", views.receipt, name="receipt"),
]
