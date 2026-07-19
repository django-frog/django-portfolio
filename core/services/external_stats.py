"""Background fetch service for GitHub and LeetCode data.

This module is the long-term home for fetching external stats used by the
portfolio. Functions here are async and meant to be driven by either:
  * the ``update_external_stats`` management command (synchronous wrapper), or
  * a background worker / scheduler added later.

Data is persisted in the Django cache for 24h under fixed keys so the cache is
shared across processes.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile

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


# ---------------------------------------------------------------------------
# Normalizers: raw API payload -> list of (label, value, color) dicts.
# Consumed by the ``sync_platform_stats`` management command.
# ---------------------------------------------------------------------------

_StatDict = dict[str, str]   # {"label": "...", "value": "...", "color": "..."}


def normalize_github_user(payload: dict[str, Any]) -> list[_StatDict]:
    """Convert a GitHub ``GET /user`` payload to PlatformStat dicts."""
    if not isinstance(payload, dict):
        return []

    def _int_or_none(value: Any) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    followers: Optional[int] = _int_or_none(payload.get("followers"))
    following: Optional[int] = _int_or_none(payload.get("following"))
    public_repos: Optional[int] = _int_or_none(payload.get("public_repos"))
    public_gists: Optional[int] = _int_or_none(payload.get("public_gists"))

    out: list[_StatDict] = []
    if followers is not None:
        out.append({"label": "Followers", "value": str(followers), "color": "blue"})
    if following is not None:
        out.append({"label": "Following", "value": str(following), "color": "gray"})
    if public_repos is not None:
        out.append({"label": "Public Repos", "value": str(public_repos), "color": "green"})
    if public_gists is not None:
        out.append({"label": "Public Gists", "value": str(public_gists), "color": "purple"})
    return out


def normalize_leetcode_combined(payload: dict[str, Any]) -> list[_StatDict]:
    """Convert the combined LeetCode payload into PlatformStat dicts.

    ``payload`` is the shape written by ``fetch_all_leetcode_data``:
    ``{"user": ..., "profile": ..., "graphql": ...}``.
    """
    if not isinstance(payload, dict):
        return []

    out: list[_StatDict] = []

    # 1) Counts come from the GraphQL `submitStatsGlobal.acSubmissionNum` list.
    graphql = payload.get("graphql") or {}
    if isinstance(graphql, dict):
        counts = (
            graphql.get("data", {}).get("matchedUser", {})
            .get("submitStatsGlobal", {})
            .get("acSubmissionNum")
        )
        if isinstance(counts, list):
            by_difficulty = {
                item.get("difficulty"): item.get("count")
                for item in counts
                if isinstance(item, dict)
            }
            total = by_difficulty.get("All")
            if isinstance(total, int):
                out.append({
                    "label": "Total Solved", "value": str(total), "color": "green",
                })
            easy = by_difficulty.get("Easy")
            if isinstance(easy, int):
                out.append({
                    "label": "Easy", "value": str(easy), "color": "green",
                })
            medium = by_difficulty.get("Medium")
            if isinstance(medium, int):
                out.append({
                    "label": "Medium", "value": str(medium), "color": "yellow",
                })
            hard = by_difficulty.get("Hard")
            if isinstance(hard, int):
                out.append({
                    "label": "Hard", "value": str(hard), "color": "red",
                })

        # Ranking -> purple badge
        profile = graphql.get("data", {}).get("matchedUser", {}).get("profile", {})
        ranking = profile.get("ranking") if isinstance(profile, dict) else None
        if isinstance(ranking, int):
            out.append({
                "label": "Ranking", "value": f"{ranking:,}", "color": "purple",
            })

    # 2) Reputation from the REST /userProfile endpoint.
    profile = payload.get("profile")
    if isinstance(profile, dict):
        reputation = profile.get("reputation")
        if isinstance(reputation, int):
            out.append({
                "label": "Reputation", "value": f"{reputation:,}", "color": "blue",
            })

    return out


async def fetch_platform_stats(
    api_identifier: str,
) -> tuple[list[_StatDict], Optional[str], Optional[bytes]]:
    """Dispatch by api_identifier and return ``(stats, avatar_url, avatar_bytes)``.

    ``avatar_url`` and ``avatar_bytes`` are only populated for GitHub today;
    other platforms return ``None`` for both.
    """
    identifier = (api_identifier or "").strip().lower()
    avatar_url: Optional[str] = None
    avatar_bytes: Optional[bytes] = None
    stats: list[_StatDict] = []

    if identifier == "github":
        raw = await fetch_github_data()
        if raw:
            stats = normalize_github_user(raw)
            avatar_url = raw.get("avatar_url")
    elif identifier == "leetcode":
        raw = await fetch_all_leetcode_data()
        if raw:
            stats = normalize_leetcode_combined(raw)
    else:
        logger.warning(
            "fetch_platform_stats: unknown api_identifier %r",
            api_identifier,
        )

    if avatar_url:
        avatar_bytes = await _download_bytes(avatar_url)

    return stats, avatar_url, avatar_bytes


async def _download_bytes(url: str, timeout: int = 15) -> Optional[bytes]:
    """Best-effort GET that returns the response body as bytes."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as exc:
        logger.error("download failed for %s: %s", url, exc)
        return None


def avatar_filename_for(url: str, platform_slug: str) -> str:
    """Return a stable on-disk filename for a fetched avatar URL."""
    path: str = urlparse(url).path
    ext: str = os.path.splitext(path)[1].lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        ext = ".png"
    digest: str = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{platform_slug}-{digest}{ext}"


def save_avatar_bytes(platform_obj: Any, image_bytes: bytes, url: str) -> bool:
    """Save ``image_bytes`` to ``platform_obj.avatar_or_logo``. Returns True on success.

    Caller is responsible for ``platform_obj.save()`` afterwards.
    """
    if not image_bytes or not url:
        return False
    try:
        filename: str = avatar_filename_for(url, platform_obj.slug or "platform")
        platform_obj.avatar_or_logo.save(
            filename,
            ContentFile(image_bytes),
            save=False,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Could not save avatar bytes for %s: %s", platform_obj, exc
        )
        return False


def ensure_media_root() -> None:
    """Create MEDIA_ROOT if it doesn't exist (idempotent)."""
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)