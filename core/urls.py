from django.urls import path
from django.conf.urls import handler404
from .views import *

app_name = "core"

urlpatterns = [
    path("", view=FrontPageView.as_view(), name="home_page"),
    path("about/", view=AboutPageView.as_view(), name="about_page"),
    path("about/github/", view=get_github_data, name="github_data")
]
