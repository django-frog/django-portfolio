from django.urls import path
from django.conf.urls import handler404
from .views import *

app_name = "core"

urlpatterns = [
    path("", view=FrontPageView.as_view(), name="home_page"),
    path("about/", view=AboutPageView.as_view(), name="about_page"),
    path("media/", view=MediaPageView.as_view(), name="media_page"),
    path("media/github/", view=get_github_data, name="github_data"),
]
