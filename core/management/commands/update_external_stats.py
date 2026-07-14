"""Management command: refresh persistent GitHub and LeetCode caches."""

from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from core.services import external_stats


class Command(BaseCommand):
    """Fetch GitHub + LeetCode data and store it in the persistent cache."""

    help: str = (
        "Fetches and caches external GitHub and LeetCode statistics "
        "for 24 hours under the 'github_data_persistent' and "
        "'leetcode_data_persistent' cache keys."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--source",
            choices=["all", "github", "leetcode"],
            default="all",
            help="Which external source(s) to refresh (default: all).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source: str = options["source"]
        results: dict[str, Any] = {}

        if source in ("all", "github"):
            self.stdout.write("Fetching GitHub data...")
            github_data = async_to_sync(external_stats.update_github_cache)()
            results["github"] = github_data
            self._report(
                label="GitHub",
                payload=github_data,
            )

        if source in ("all", "leetcode"):
            self.stdout.write("Fetching LeetCode data...")
            leetcode_data = async_to_sync(external_stats.update_leetcode_cache)()
            results["leetcode"] = leetcode_data
            self._report(
                label="LeetCode",
                payload=leetcode_data,
            )

        self.stdout.write(self.style.SUCCESS("Done."))

    def _report(self, *, label: str, payload: Any) -> None:
        if payload is None:
            self.stdout.write(
                self.style.ERROR(
                    f"{label} fetch failed; cached data (if any) was preserved."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"{label} data fetched and cached successfully."
            )
        )