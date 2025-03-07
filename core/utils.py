from django.core.cache import cache
from django.core import paginator
from django.conf import settings

import httpx


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

async def fetch_graphql_leetcode_data(cache_key):
    """
    Fetches and parses data from LeetCode GraphQL API.

    Returns:
        dict: A dictionary containing the account name, profile image URL,
              and the number of problems solved (easy, medium, hard).
              Returns None if an error occurs.
    """
    cache_timeout_secs = 60 * 15
    data = cache.get(cache_key)
    if data:
        return data
    
    # Define the GraphQL API endpoint
    leetcode_api = settings.LEETCODE_GRAPHQL_API

    # GraphQL query to fetch user profile details
    GRAPHQL_QUERY = """
    query getUserProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
              realName
              userAvatar
              ranking
            }
            submitStatsGlobal {
              acSubmissionNum {
                difficulty
                count
              }
            }
        }
    }
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            leetcode_api,
            json={"query": GRAPHQL_QUERY, "variables": {"username": settings.LEETCODE_USERNAME}},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        user_data = data["data"]["matchedUser"]
        cache.set(cache_key, user_data, timeout=cache_timeout_secs)

        return user_data


async def fetch_rest_leetcode_user(cache_key):
    """
    Fetches and parses profile's data from LeetCode REST API.

    Returns:
        dict: A dictionary containing the account name, profile image URL.
    """
    cache_timeout_secs = 60 * 15
    data = cache.get(cache_key)
    if data:
        return data
    
    # Define the REST API endpoint
    leetcode_api = settings.LEETCODE_REST_API
    user_endpoint = leetcode_api + settings.LEETCODE_USERNAME

    async with httpx.AsyncClient() as client:
        response = await client.get(
            user_endpoint,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        user_data = response.json()
        cache.set(cache_key, user_data, timeout=cache_timeout_secs)

        return user_data


async def fetch_rest_leetcode_profile(cache_key):
    """
    Fetches and parses solved problems from LeetCode REST API.

    Returns:
        dict: A dictionary containing the account name, profile image URL.
    """
    cache_timeout_secs = 60 * 15
    data = cache.get(cache_key)
    if data:
        return data
    
    # Define the REST API endpoint
    leetcode_api = settings.LEETCODE_REST_API
    problems_endpoint = leetcode_api + "userProfile/" + settings.LEETCODE_USERNAME

    async with httpx.AsyncClient() as client:
        response = await client.get(
            problems_endpoint,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        problems_data = response.json()
        cache.set(cache_key, problems_data, timeout=cache_timeout_secs)

        return problems_data



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
