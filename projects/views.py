from django.shortcuts import render
from .models import Project, ProjectTag
from django.core.cache import cache
from django.views.decorators.http import require_GET
from asgiref.sync import sync_to_async
from core.utils import paginate

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

@require_GET
@sync_to_async
def list_projects(request):
    """
    Lists all projects with pagination.

    Args:
        request: The HTTP request object.

    Returns:
        A rendered template with paginated projects and search context.
    """
    page_query = request.GET.get("page" , "1")
    page_num = int(page_query) if page_query.isnumeric() else 1

    projects = Project.objects\
        .filter(deleted_at = None)\
            .order_by('-created_at')\
                .prefetch_related('tags')
    
    projects_context = paginate(projects, current_page=page_num)
    template = "projects/project_page.html"

    search_context = search_bar_context()
    
    context = {
        "projects" : projects_context,
        "search_bar" : search_context,
    }
    return render(request, template, context)

@require_GET
def search_projects(request):
    """
    Filters projects based on title and tags.

    Args:
        request: The HTTP request object.

    Returns:
        A rendered template with filtered projects and search context.
    """
    title_query = request.GET.get("title" , "")
    tags_query = request.GET.getlist("tags" , [])
    tags = [int(tag) for tag in tags_query]

    
    selected_projects = Project.objects.filter(
        deleted_at = None,
        title__contains=title_query,
    ).order_by("-created_at").prefetch_related('tags')

    if tags:
        selected_projects = selected_projects.filter(
            tags__in = tags
        )

    projects_context = paginate(selected_projects)
    search_context = search_bar_context()

    template = "projects/project_page.html"

    context = {
        "projects" : projects_context,
        "search_bar" : search_context
    }
    return render(request, template, context)
