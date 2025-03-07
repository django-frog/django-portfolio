from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
from django.core.cache import cache
from django.views import generic
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from django.utils.translation import activate
from asgiref.sync import async_to_sync

import httpx

from .utils import fetch_github_data, fetch_leetcode_data

# Create your views here.
@require_GET
@async_to_sync
async def get_github_data(request):
    """
        Connect with Github API to get account information.

        Args:
            HTTP Request
            
        Rseturns:
            JSON Response 
    """
    if not settings.GITHUB_API_TOKEN:
        return JsonResponse({
            "error" : "API token is not set"
        }, status=500)

    user_resource_url = settings.GITHUB_API + "user"
    github_cache_key = "github_data"

    try:
        github_account_data = await fetch_github_data(
            api_url= user_resource_url,
            token=settings.GITHUB_API_TOKEN,
            cache_key=github_cache_key
        )
        
        return JsonResponse(github_account_data)
    
    except httpx.HTTPStatusError as e:
            return JsonResponse({"error": str(e)}, status=e.response.status_code)
    
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)

@require_GET
@async_to_sync
async def get_leetcode_data(request):
    leetcode_cache_key = "leecode_data"
    try:
        leetcode_data = await fetch_leetcode_data(cache_key=leetcode_cache_key)
        return JsonResponse(leetcode_data)
    except httpx.HTTPStatusError as e:
            return JsonResponse({"error": str(e)}, status=e.response.status_code)
    
    except Exception as e:
        print(e)
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)

@require_GET
def switch_language(request):
    """
    Custom set language view.

    Args:
        request (HttpRequest): HTTP request with 'lang' query parameter.

    Returns:
        HttpResponseRedirect: Redirects to the referring page.
    """
    lang_code = request.GET.get("lang", "en")  # Get language from query string

    activate(lang_code)  # Activate language for the current request

    # Store language in session
    request.session["django_language"] = lang_code
    request.session.modified = True  # Ensure the session is updated

    # Set language in a cookie
    response = redirect(request.META.get("HTTP_REFERER", "/"))
    response.set_cookie(
        "django_language",  # Correct language cookie name
        lang_code,
        max_age=getattr(settings, "LANGUAGE_COOKIE_AGE", 31536000),  # Default: 1 year
        path="/",
    )

    return response

class FrontPageView(generic.TemplateView):
    """
        Front-Page View Class.
    """
    template_name = "portfolio/front_page.html"

class AboutPageView(generic.TemplateView):
    """
        About-Page View Class.
    """
    template_name = "portfolio/about_page.html"

class ProjectsPageView(generic.TemplateView):
    """
        Project-Page View Class
    """
    template_name = "portfolio/project_page.html"

class MediaPageView(generic.TemplateView):
    """
        SocailMedia-Page View Class
    """
    template_name = "portfolio/media_page.html"

class Page404View(generic.TemplateView):
    """
        Page Not Found (404) Custom Handler
    """
    template_name = "portfolio/404.html"

class Page500View(generic.TemplateView):
    """
        Server Error (500) Custom Handler
    """
    template_name = "portfolio/500.html"

class HomePageRedirectView(generic.RedirectView):
    """
        Home Page Redirect View.
    """
    pattern_name = "core:home_page"