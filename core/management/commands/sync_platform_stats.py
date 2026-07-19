"""Sync PlatformStat rows from external APIs.

For every active ``SocialPlatform`` of type ``stat_driven``, dispatch to the
matching fetcher in ``core.services.external_stats`` (selected via the
``api_identifier`` field), normalise the raw payload into
``(label, value, color)`` triples, and upsert ``PlatformStat`` rows so the
Media page renders live data.

GitHub additionally downloads the user avatar and saves it to
``SocialPlatform.avatar_or_logo`` if no custom image has been uploaded.

Run::

    python manage.py sync_platform_stats
"""

from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand, CommandError

from core.models import PlatformStat, SocialPlatform
from core.services.external_stats import (
    fetch_platform_stats,
    ensure_media_root,
    save_avatar_bytes,
)


_KNOWN_IDENTIFIERS: frozenset[str] = frozenset({"github", "leetcode"})

_VALID_COLORS: frozenset[str] = frozenset({
    "green", "yellow", "red", "blue", "purple", "gray",
})


class Command(BaseCommand):
    """Fetch external platform stats and persist them to the database."""

    help: str = (
        "Fetches live stats for every active stat-driven SocialPlatform "
        "(GitHub, LeetCode, ...) and updates the linked PlatformStat rows. "
        "Also downloads and saves the GitHub avatar when available."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--platform",
            action="append",
            dest="platforms",
            help=(
                "Limit the sync to one or more platform slugs "
                "(repeatable, e.g. --platform github --platform leetcode)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and normalise stats but do not write to the database.",
        )
        parser.add_argument(
            "--skip-avatars",
            action="store_true",
            help="Do not download/save avatars (useful for sandboxed CI).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        platforms_qs = SocialPlatform.objects.filter(
            is_active=True,
            platform_type="stat_driven",
        )
        if options.get("platforms"):
            platforms_qs = platforms_qs.filter(slug__in=options["platforms"])

        platforms: list[SocialPlatform] = list(
            platforms_qs.order_by("sort_order", "name")
        )
        if not platforms:
            self.stdout.write(
                self.style.WARNING("No active stat-driven platforms to sync.")
            )
            return

        dry_run: bool = bool(options.get("dry_run"))
        skip_avatars: bool = bool(options.get("skip_avatars"))

        if not dry_run and not skip_avatars:
            ensure_media_root()

        self.stdout.write(
            self.style.NOTICE(
                f"Syncing {len(platforms)} platform(s)"
                f"{' (dry run)' if dry_run else ''}..."
            )
        )

        overall_failures: int = 0
        for platform in platforms:
            identifier: str = (platform.api_identifier or "").strip().lower()
            if not identifier:
                self.stdout.write(
                    self.style.WARNING(
                        f"  · {platform.name}: skipped (no api_identifier set)"
                    )
                )
                continue

            if identifier not in _KNOWN_IDENTIFIERS:
                self.stdout.write(
                    self.style.WARNING(
                        f"  · {platform.name}: skipped "
                        f"(api_identifier={identifier!r} is not supported; "
                        f"supported: {sorted(_KNOWN_IDENTIFIERS)})"
                    )
                )
                overall_failures += 1
                continue

            self.stdout.write(f"  · {platform.name} ({identifier})...", ending=" ")
            try:
                stats, avatar_url, avatar_bytes = async_to_sync(
                    fetch_platform_stats
                )(identifier)
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(
                    self.style.ERROR(f"fetch failed: {exc}")
                )
                overall_failures += 1
                continue

            if not stats:
                self.stdout.write(
                    self.style.WARNING(
                        "no stats returned (network or upstream error?)"
                    )
                )
                overall_failures += 1
                continue

            if dry_run:
                for stat in stats:
                    self.stdout.write(
                        f"\n      [dry-run] {stat['label']}: {stat['value']} "
                        f"(color={stat['color']})"
                    )
                continue

            created, updated = self._upsert_stats(platform, stats)
            avatar_msg: str = ""
            if not skip_avatars and avatar_url and avatar_bytes:
                if not platform.avatar_or_logo:
                    if save_avatar_bytes(platform, avatar_bytes, avatar_url):
                        avatar_msg = " + avatar downloaded"
                else:
                    avatar_msg = " (avatar already set, skipped)"

            platform.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"upserted {created} new / {updated} updated stat(s)"
                    f"{avatar_msg}"
                )
            )

        if overall_failures:
            raise CommandError(
                f"{overall_failures} platform(s) had issues; see output above."
            )
        self.stdout.write(self.style.SUCCESS("Done."))

    def _upsert_stats(
        self,
        platform: SocialPlatform,
        stats: list[dict[str, str]],
    ) -> tuple[int, int]:
        """Create/update PlatformStat rows for ``platform``. Returns (created, updated)."""
        existing: dict[str, PlatformStat] = {
            stat.label: stat for stat in platform.stats.all()
        }

        created: int = 0
        updated: int = 0
        seen_labels: set[str] = set()

        for index, stat_data in enumerate(stats):
            label: str = stat_data.get("label", "").strip()
            value: str = str(stat_data.get("value", "")).strip()
            color: str = stat_data.get("color", "gray").strip().lower()
            if not label or not value:
                continue
            if color not in _VALID_COLORS:
                color = "gray"
            seen_labels.add(label)

            existing_stat = existing.get(label)
            if existing_stat is None:
                PlatformStat.objects.create(
                    platform=platform,
                    label=label,
                    value=value,
                    stat_color=color,
                    sort_order=index * 10,
                )
                created += 1
            else:
                changed: bool = False
                if existing_stat.value != value:
                    existing_stat.value = value
                    changed = True
                if existing_stat.stat_color != color:
                    existing_stat.stat_color = color
                    changed = True
                if existing_stat.sort_order != index * 10:
                    existing_stat.sort_order = index * 10
                    changed = True
                if changed:
                    existing_stat.save(
                        update_fields=["value", "stat_color", "sort_order"],
                    )
                    updated += 1

        # Drop stats that no longer exist upstream so the card stays clean.
        stale: list[PlatformStat] = [
            existing[label] for label in existing
            if label not in seen_labels
        ]
        if stale:
            for stat in stale:
                stat.delete()
            self.stdout.write(
                self.style.WARNING(
                    f"    pruned {len(stale)} stale stat(s)"
                )
            )

        return created, updated