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

import httpx
import logging
from json import loads
from typing import Any

from .forms import ContactInquiryForm
from .models import ContactInquiry, SocialPlatform, TechnicalDomain, WorkExperience
from .services.ai import AIServiceError, generate_portfolio_response
from .services.external_stats import (
    GITHUB_CACHE_KEY,
    LEETCODE_CACHE_KEY,
    fetch_github_data,
    update_leetcode_cache,
)

logger = logging.getLogger(__name__)

# Create your views here.
@require_GET
def get_github_data(request):
    """
    Return the cached GitHub account data, or a clean JSON error.

    This view is read-only: it never blocks the page render on a network
    call. It reads the persistent cache populated by the
    ``update_external_stats`` management command. If the cache is empty
    (e.g., first request after a deploy, before the cron has run), a
    synchronous fallback fetch is attempted exactly once. If that fails,
    a 503 JSON error is returned.
    """
    data = cache.get(GITHUB_CACHE_KEY)
    if data is None:
        try:
            data = async_to_sync(fetch_github_data)()
        except Exception as exc:
            logger.exception("GitHub fallback fetch failed: %s", exc)
            data = None

    if data is None:
        return JsonResponse(
            {"error": "Data warming up, please try again soon"},
            status=503,
        )
    return JsonResponse(data)


@require_GET
def get_leetcode_data(request):
    """
    Return the cached LeetCode data, or a clean JSON error.

    Like ``get_github_data``, this is fully decoupled from the upstream
    API. It reads the persistent cache and only falls back to a
    synchronous fetch when the cache is empty.
    """
    data = cache.get(LEETCODE_CACHE_KEY)
    if data is None:
        try:
            data = async_to_sync(update_leetcode_cache)()
        except Exception as exc:
            logger.exception("LeetCode fallback fetch failed: %s", exc)
            data = None

    if data is None:
        return JsonResponse(
            {"error": "Data warming up, please try again soon"},
            status=503,
        )
    return JsonResponse(data)


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

    try:
        answer = generate_portfolio_response(question)
    except AIServiceError as exc:
        return JsonResponse(
            {"error": "AI request failed", "details": str(exc)},
            status=500,
        )

    return JsonResponse({
        "question": question,
        "reply": answer,
    })


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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["experiences"] = WorkExperience.objects.all()
        return context

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
        Social Media & Coding Platforms page.
    """
    template_name = "portfolio/media_page.html"

    _STAT_COLOR_CLASSES: dict[str, dict[str, str]] = {
        "green":  {
            "border": "border-emerald-500",
            "text":   "text-emerald-700 dark:text-emerald-300",
            "bg":     "bg-emerald-50 dark:bg-emerald-900/30",
        },
        "yellow": {
            "border": "border-yellow-500",
            "text":   "text-yellow-700 dark:text-yellow-300",
            "bg":     "bg-yellow-50 dark:bg-yellow-900/30",
        },
        "red":    {
            "border": "border-red-500",
            "text":   "text-red-700 dark:text-red-300",
            "bg":     "bg-red-50 dark:bg-red-900/30",
        },
        "blue":   {
            "border": "border-blue-500",
            "text":   "text-blue-700 dark:text-blue-300",
            "bg":     "bg-blue-50 dark:bg-blue-900/30",
        },
        "purple": {
            "border": "border-purple-500",
            "text":   "text-purple-700 dark:text-purple-300",
            "bg":     "bg-purple-50 dark:bg-purple-900/30",
        },
        "gray":   {
            "border": "border-gray-400",
            "text":   "text-gray-700 dark:text-gray-300",
            "bg":     "bg-gray-50 dark:bg-gray-800/50",
        },
    }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        stat_platforms = (
            SocialPlatform.objects
            .filter(is_active=True, platform_type="stat_driven")
            .prefetch_related("stats")
            .order_by("sort_order", "name")
        )
        for platform in stat_platforms:
            for stat in platform.stats.all():
                stat.color_classes = self._STAT_COLOR_CLASSES.get(
                    stat.stat_color,
                    self._STAT_COLOR_CLASSES["gray"],
                )

        context["stat_platforms"] = stat_platforms
        context["simple_platforms"] = (
            SocialPlatform.objects
            .filter(is_active=True, platform_type="simple_link")
            .order_by("sort_order", "name")
        )
        return context

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