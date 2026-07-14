from django.conf import settings
from django.http import JsonResponse
from django.http import HttpResponse
from django.core.cache import cache
from django.views import generic
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.shortcuts import redirect, render
from django.utils.translation import activate
from django.contrib import messages
from asgiref.sync import async_to_sync
from django_ratelimit.decorators import ratelimit
from openai import OpenAI

import httpx
from json import loads
from typing import Any

from .forms import ContactInquiryForm
from .models import ContactInquiry, TechnicalDomain, WorkExperience
from .utils import *

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
    graphql_option = request.GET.get("graphql" , "")
    try:
        if graphql_option:
            leetcode_cache_key = "leetcode_data"
            leetcode_data = await fetch_graphql_leetcode_data(cache_key=leetcode_cache_key)
            return JsonResponse(leetcode_data)
        else:
            leetcode_user_cache_key = "leetcode_user_data"
            leetcode_problems_cache_key = "leetcode_problems_data"

            leetcode_user_data = await fetch_rest_leetcode_user(cache_key=leetcode_user_cache_key)
            leetcode_profile_data = await fetch_rest_leetcode_profile(cache_key=leetcode_problems_cache_key)
            return JsonResponse({
                "user" : leetcode_user_data,
                "profile" : leetcode_profile_data
            })
            
    except httpx.HTTPStatusError as e:
            return JsonResponse({"error": str(e)}, status=e.response.status_code)

    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)


def rate_limit_view(request, exception=None):
    """
    Standard JSON response used when a request exceeds rate limits.
    """

    details = str(exception) if exception else ""

    return JsonResponse({
        "error": "You exceeded the maximum allowed requests",
        "message": "You exceeded the maximum allowed requests. Please wait before trying again.",
        "details": details,
    }, status=429)


@require_POST
@ratelimit(key="ip", rate="3/1h", block=True)
def ai_chatbot(request):

    try:
        body = loads(request.body.decode("utf-8"))
        question = body.get("question", "").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    if not question:
        return JsonResponse({"error": "Missing 'question' field"}, status=400)

    # Initialize OpenAI client
    try:
        client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=settings.HF_TOKEN,
        )
    except Exception as e:
        return JsonResponse({"error": "Failed to init AI client", "details": str(e)}, status=500)

    # Enhanced context
    PORTFOLIO_CONTEXT = (
        "Mohammad Hamdan is a senior full-stack engineer specializing in Django, Python, "
        "database design, Odoo (ERP), and modern front-end development using TailwindCSS and Alpine.js. "
        "He builds scalable, clean, and maintainable systems with a strong focus on performance and UX. "

        "He has deep experience across: "
        "• Backend engineering (Django, DRF, PostgreSQL, Redis, Celery). "
        "• Odoo development (HR, Payroll, Accounting, Custom Modules, Integrations). "
        "• Data engineering (ETL pipelines, Prefect, automation). "
        "• Front-end design using TailwindCSS, Alpine.js, and responsive UI/UX. "

        "Key traits: extremely detail-oriented, solves complex problems, strong architecture sense, "
        "writes clean code, and focuses on delivering production-quality solutions. "

        "All answers must be short, clear, and strictly based on this context only and only with 120 tokens."
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are Mohammad's portfolio assistant. "
                "Use ONLY the provided context. "
                "Keep answers short, direct, and easy to read. "
                f"Context: {PORTFOLIO_CONTEXT}"
            ),
        },
        {"role": "user", "content": question},
    ]

    try:
        completion = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2:featherless-ai",
            messages=messages,
            temperature=0.1,
            max_tokens=120,
        )

        answer = completion.choices[0].message.content.strip()

        return JsonResponse({
            "question": question,
            "reply": answer,
        })

    except Exception as e:
        return JsonResponse({"error": "AI request failed", "details": str(e)}, status=500)


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

        Renders the about page with the dynamic, database-driven
        technical domains / skills and work-experience timeline.
    """
    template_name = "portfolio/about_page.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["domains"] = (
            TechnicalDomain.objects
            .prefetch_related("skills")
            .all()
        )
        context["experiences"] = WorkExperience.objects.all()
        return context

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


def _get_client_ip(request) -> str | None:
    """Return the originating client IP, honouring common proxy headers."""
    forwarded_for: str | None = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@ratelimit(key="ip", rate="5/1h", block=True)
@require_http_methods(["GET", "POST"])
def contact_view(request):
    """
        Public contact form view.

        Renders the contact template on GET; on POST, validates the
        ``ContactInquiryForm``, records the client IP, and saves the
        inquiry. Rate-limited to 5 submissions per IP per hour.
    """
    is_ajax: bool = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if request.method == "POST":
        form = ContactInquiryForm(request.POST)
        if form.is_valid():
            inquiry: ContactInquiry = form.save(commit=False)
            inquiry.ip_address = _get_client_ip(request)
            inquiry.save()

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Thank you! Your inquiry has been received.",
                    },
                    status=201,
                )

            messages.success(
                request,
                "Thank you! Your inquiry has been received. "
                "I'll get back to you shortly.",
            )
            return redirect("core:contact_page")

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "errors": form.errors,
                },
                status=400,
            )
    else:
        form = ContactInquiryForm()

    return render(
        request,
        "portfolio/contact_page.html",
        {"form": form},
    )