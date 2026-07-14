from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Project, ProjectTag


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_featured",
        "start_date",
        "created_at",
        "deleted_at",
    )
    list_filter = ("is_featured", "tags", "created_at", "deleted_at")
    search_fields = ("title", "short_description", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "deleted_at")
    list_editable = ("is_featured",)
    date_hierarchy = "created_at"
    filter_horizontal = ("tags",)
    save_on_top = True

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "short_description",
                    "content",
                    "thumbnail",
                ),
            },
        ),
        (
            _("Links"),
            {
                "fields": (
                    "project_url",
                    "repository_url",
                    "live_demo_url",
                ),
            },
        ),
        (
            _("Project Details"),
            {
                "fields": (
                    "tags",
                    "start_date",
                    "end_date",
                    "is_featured",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "deleted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Soft delete selected projects")
    def soft_delete_selected(
        self,
        request: HttpRequest,
        queryset: QuerySet[Project],
    ) -> None:
        now = timezone.now()
        updated: int = queryset.filter(deleted_at__isnull=True).update(
            deleted_at=now
        )
        self.message_user(
            request,
            f"{updated} project(s) were soft-deleted.",
        )

    @admin.action(description="Restore selected projects")
    def restore_selected(
        self,
        request: HttpRequest,
        queryset: QuerySet[Project],
    ) -> None:
        updated: int = queryset.filter(
            deleted_at__isnull=False
        ).update(deleted_at=None)
        self.message_user(
            request,
            f"{updated} project(s) were restored.",
        )

    actions: tuple[str, ...] = ("soft_delete_selected", "restore_selected")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Project]:
        return super().get_queryset(request).prefetch_related("tags")