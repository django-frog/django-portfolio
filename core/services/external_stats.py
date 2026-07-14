"""Background fetch service for GitHub and LeetCode data.

This module is the long-term home for fetching external stats used by the
portfolio. Functions here are async and meant to be driven by either:
  * the ``update_external_stats`` management command (synchronous wrapper), or
  * a background worker / scheduler added later.

Data is persisted in the Django cache for 24h under fixed keys so the cache is
shared across processes.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

GITHUB_CACHE_KEY = "github_data_persistent"
LEETCODE_CACHE_KEY = "leetcode_data_persistent"

PERSISTENT_TIMEOUT_SECONDS: int = 60 * 60 * 24

_LEETCODE_GRAPHQL_QUERY: str = """
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


async def fetch_github_data(
    api_url: Optional[str] = None,
    token: Optional[str] = None,
    timeout: int = 10,
) -> Optional[dict[str, Any]]:
    """Fetch data from the GitHub API and cache it for 24h.

    Args:
        api_url: Endpoint to hit. Falls back to ``settings.GITHUB_API``.
        token: GitHub token. Falls back to ``settings.GITHUB_TOKEN``.
        timeout: HTTP timeout in seconds.

    Returns:
        The cached/ fetched payload as a dict, or ``None`` on error.
        On error, the existing cached value (if any) is preserved.
    """
    api_url = api_url or settings.GITHUB_API
    token = token or settings.GITHUB_TOKEN

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "DjangoDev Application",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(GITHUB_CACHE_KEY, data, timeout=PERSISTENT_TIMEOUT_SECONDS)
            return data
    except httpx.HTTPError as exc:
        logger.error(
            "GitHub fetch failed for %s: %s",
            api_url,
            exc,
            exc_info=True,
        )
        return None


async def fetch_graphql_leetcode_data(
    username: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Fetch the LeetCode user profile via the GraphQL endpoint.

    Returns the raw ``matchedUser`` payload, or ``None`` on error.
    """
    username = username or settings.LEETCODE_USERNAME

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.LEETCODE_GRAPHQL_API,
                json={
                    "query": _LEETCODE_GRAPHQL_QUERY,
                    "variables": {"username": username},
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", {}).get("matchedUser")
    except httpx.HTTPError as exc:
        logger.error(
            "LeetCode GraphQL fetch failed for %s: %s",
            username,
            exc,
            exc_info=True,
        )
        return None


async def fetch_rest_leetcode_user(
    username: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Fetch LeetCode REST user profile data, or ``None`` on error."""
    username = username or settings.LEETCODE_USERNAME
    endpoint = settings.LEETCODE_REST_API + username

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.error(
            "LeetCode REST user fetch failed for %s: %s",
            username,
            exc,
            exc_info=True,
        )
        return None


async def fetch_rest_leetcode_profile(
    username: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """Fetch LeetCode REST solved-problems profile, or ``None`` on error."""
    username = username or settings.LEETCODE_USERNAME
    endpoint = settings.LEETCODE_REST_API + "userProfile/" + username

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.error(
            "LeetCode REST profile fetch failed for %s: %s",
            username,
            exc,
            exc_info=True,
        )
        return None


async def fetch_all_leetcode_data() -> Optional[dict[str, Any]]:
    """Fetch all LeetCode endpoints and cache them as a single payload.

    Returns the cached dict, or ``None`` if every endpoint failed.
    On partial failure, the successfully fetched parts are still cached
    under ``LEETCODE_CACHE_KEY`` so the UI sees something useful.
    """
    user_data = await fetch_rest_leetcode_user()
    profile_data = await fetch_rest_leetcode_profile()
    graphql_data = await fetch_graphql_leetcode_data()

    if user_data is None and profile_data is None and graphql_data is None:
        logger.error("All LeetCode fetches failed; not updating cache.")
        return None

    combined: dict[str, Any] = {
        "user": user_data,
        "profile": profile_data,
        "graphql": graphql_data,
    }
    cache.set(
        LEETCODE_CACHE_KEY,
        combined,
        timeout=PERSISTENT_TIMEOUT_SECONDS,
    )
    return combined


async def update_github_cache() -> Optional[dict[str, Any]]:
    """Refresh only the GitHub cache."""
    return await fetch_github_data()


async def update_leetcode_cache() -> Optional[dict[str, Any]]:
    """Refresh only the LeetCode cache."""
    return await fetch_all_leetcode_data()


async def update_all_external_stats() -> dict[str, Optional[dict[str, Any]]]:
    """Refresh both GitHub and LeetCode caches. Returns the results dict."""
    github = await update_github_cache()
    leetcode = await update_leetcode_cache()
    return {"github": github, "leetcode": leetcode}