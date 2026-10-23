"""urls.py - /licences/ URLs."""

from django.urls import path

from . import views

app_name = "licensing"
urlpatterns = [
    path("", views.licence_list, name="licence_list"),
    path("keys/", views.key_generator, name="key_generator"),
    path("<int:school_id>/key/", views.apply_key, name="apply_key_for"),
    path("<int:school_id>/pack/", views.apply_pack, name="apply_pack_for"),
    path("<int:school_id>/discount/", views.set_discount, name="set_discount"),
    path("my/", views.my_licence, name="my_licence"),
    path("my/key/", views.apply_key, name="apply_key"),
    path("my/pack/", views.apply_pack, name="apply_pack"),
]
