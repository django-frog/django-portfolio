import httpx
from django.core.cache import cache
from django.core import paginator

async def fetch_github_data(api_url, token, cache_key, timeout=10):
    """
        Fetch data from Github API.
        
        Args:
            api_url: the end-point that you want to hit
            token: API token
            timeout: connection time-out
        
        Returns:
            Github Data as Dict()
    """
    cache_timeout_secs = 60 * 15
    data = cache.get(cache_key)
    if data:
        return data
    
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers={
            "Authorization" : f"Bearer {token}",
            "User-Agent" : "DjangoDev Application"
        }, timeout=timeout)

        response.raise_for_status()
        data = response.json()
        cache.set(cache_key, data, timeout=cache_timeout_secs)
        return data


def paginate(queryset, page_size = 5, current_page = 1):
    """
    Paginates a queryset and returns context for rendering in templates.

    Args:
        queryset: The queryset to paginate.
        page_size: Number of items per page.
        current_page: The current page number.

    Returns:
        A dictionary containing pagination context.
    """
    paginator_obj = paginator.Paginator(queryset, page_size)
    pages_n = paginator_obj.num_pages

    current_page = max(1 , min(current_page , pages_n))

    try:
        projects_page = paginator_obj.get_page(current_page)
        
    except paginator.PageNotAnInteger:
        projects_page = paginator_obj.get_page(1)

    except paginator.EmptyPage:
        projects_page = paginator_obj.page(pages_n)

    context = {
        "current_page" : projects_page.number,
        "next_page" : projects_page.next_page_number() if projects_page.has_next() else None,
        "prev_page" : projects_page.previous_page_number() if projects_page.has_previous() else None,
        "last_page" : pages_n,
        "page_indices" : range(1, pages_n + 1),
        "data" : projects_page,
    }

    return context
