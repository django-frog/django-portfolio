from django.core.cache import cache
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
    """View to display a paginated list of projects."""
    paginate_by = 5
    model = Project
    template_name = "projects/project_page.html"
    context_object_name = "projects"

    def get_queryset(self):
        """Retrieve non-deleted projects ordered by creation date."""
        return super().get_queryset()\
            .filter(Q(deleted_at__isnull=True))\
                .order_by('-created_at')\
                    .prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Add the search bar context to the template."""
        context = super().get_context_data(**kwargs)
        context["search_bar"] = search_bar_context()
        return context
    

class ProjectsSearchView(generic.ListView):
    """View to display a filtered list of projects based on search criteria."""
    context_object_name = "projects"
    paginate_by = 5
    template_name = "projects/project_page.html"
    model = Project

    def get_queryset(self):
        """Filter projects based on title and tags."""
        title_query = self.request.GET.get("title", "")
        tags_query = self.request.GET.getlist("tags" , [])
        try:
            tags = [int(tag) for tag in tags_query]
        except ValueError:
            tags = []   # Ignore invalid tag values

        title_queryObj = Q(
            deleted_at = None,
            title__contains=title_query,
        )
        
        tags_queryObj =  Q(
            tags__in = tags
        ) if tags else Q()

        projects_queryset =  super().get_queryset()

        # Apply filters and return sorted results
        return projects_queryset.filter(
            title_queryObj & tags_queryObj
        ).distinct().order_by("-created_at").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        """Add search parameters and search bar context to the template."""
        context = super().get_context_data(**kwargs)

        # Build query string for pagination & filters
        title_query = self.request.GET.get("title")
        tags_queries = self.request.GET.getlist("tags" , [])
        query_params = []

        if title_query:
            query_params.append(f"title={title_query}")
        query_params.extend(f"tags={tag}" for tag in tags_queries)

        context["query_string"] = "&".join(query_params)
        context["search_bar"] = search_bar_context()
        return context
    