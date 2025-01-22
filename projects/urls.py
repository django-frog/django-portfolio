from django.urls import path
from .views import list_projects, search_projects

app_name = "projects"

urlpatterns = [
    path("", view=list_projects, name="projects_page"),
    path("search/" , view=search_projects, name="projects_search")
]
