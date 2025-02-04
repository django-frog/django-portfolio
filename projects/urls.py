from django.urls import path
from .views import ProjectsListView, ProjectsSearchView

app_name = "projects"

urlpatterns = [
    path("", view=ProjectsListView.as_view(), name="projects_page"),
    path("search/" , view=ProjectsSearchView.as_view(), name="projects_search")
]
