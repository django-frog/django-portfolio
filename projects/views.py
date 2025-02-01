from django.shortcuts import render
from django.core.cache import cache
from django.views.decorators.http import require_GET
from core.utils import paginate
from django.views import generic
from django.db.models import Q

from .models import Project, ProjectTag
# Create your views here.

def search_bar_context():
    """
    Fetches and caches search tags for the search bar.

    Returns:
        A dictionary containing search tags.
    """
    search_tags = cache.get('search_tags')
    tags_timeout = 60 * 15
    if not search_tags:
        search_tags = ProjectTag.objects.defer("created_at")
        cache.set('search_tags', search_tags, timeout=tags_timeout)
    context = {
        "search_tags" : search_tags
    }

    return context

class ProjectsListView(generic.ListView):
    paginate_by = 5
    model = Project
    template_name = "projects/project_page.html"
    context_object_name = "projects"

    def get_queryset(self):
        return super().get_queryset()\
            .filter(deleted_at=None)\
                .order_by('-created_at')\
                    .prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_bar"] = search_bar_context()
        return context
    

class ProjectsSearchView(generic.ListView):
    context_object_name = "projects"
    paginate_by = 5
    template_name = "projects/project_page.html"
    model = Project

    def get_queryset(self):
        title_query = self.request.GET.get("title", "")
        tags_query = self.request.GET.getlist("tags" , [])
        tags = [int(tag) for tag in tags_query]

        title_queryObj = Q(
            deleted_at = None,
            title__contains=title_query,
        )
        
        tags_queryObj =  Q(
            tags__in = tags
        ) if tags else Q()

        projects_queryset =  super().get_queryset()

        return projects_queryset.filter(
            title_queryObj & tags_queryObj
        ).order_by("-created_at").prefetch_related("tags")

    def get_context_data(self, **kwargs) -> dict[str]:
        context = super().get_context_data(**kwargs)
        context["search_bar"] = search_bar_context()
        return context
    