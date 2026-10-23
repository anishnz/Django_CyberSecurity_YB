"""urls.py - Account URLs (/accounts/...). Owner: Anish Shrestha."""
from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot/", views.forgot_password, name="forgot"),
    path("reset/<str:uidb64>/<str:token>/", views.reset_confirm, name="reset_confirm"),
    path("home/", views.home, name="home"),
    path("password/", views.password_change, name="password_change"),
    path("mfa/verify/", views.mfa_verify, name="mfa_verify"),
    path("mfa/setup/", views.mfa_setup, name="mfa_setup"),
    path("mfa/disable/", views.mfa_disable_self, name="mfa_disable_self"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_edit, name="user_new"),
    path("users/temporary/", views.user_temporary, name="user_temporary"),
    path("users/<int:pk>/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle, name="user_toggle"),
    path("users/<int:pk>/password/", views.user_reset_password, name="user_reset"),
    path("users/<int:pk>/security/", views.user_mfa_admin, name="user_security"),
    path("users/<int:pk>/login-as/", views.login_as, name="login_as"),
    path("login-as/stop/", views.login_as_stop, name="login_as_stop"),
    path("demo-accounts/", views.demo_accounts, name="demo_accounts"),
]
