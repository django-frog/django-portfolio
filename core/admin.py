from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    ContactInquiry,
    PlatformStat,
    Skill,
    SocialPlatform,
    TechnicalDomain,
    WorkExperience,
)


class SkillInline(admin.TabularInline):
    """Edit Skills directly under their parent TechnicalDomain."""

    model = Skill
    fields = ("name", "proficiency", "is_featured", "sort_order")
    extra = 1
    autocomplete_fields: tuple[str, ...] = ()


@admin.register(TechnicalDomain)
class TechnicalDomainAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("name", "description")
    inlines = [SkillInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "proficiency", "is_featured", "sort_order")
    list_filter = ("domain", "is_featured")
    list_editable = ("proficiency", "is_featured", "sort_order")
    search_fields = ("name",)


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = (
        "role_title",
        "company",
        "start_date",
        "end_date",
        "is_current",
    )
    list_filter = ("is_current", "start_date")
    search_fields = ("company", "role_title", "description")
    list_editable = ("is_current",)
    date_hierarchy = "start_date"
    autocomplete_fields: tuple[str, ...] = ()

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "role_title",
                    "company",
                    "company_url",
                    "location",
                ),
            },
        ),
        (
            "Timeline",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "is_current",
                ),
            },
        ),
        (
            "Details",
            {
                "fields": ("description",),
            },
        ),
    )


class PlatformStatInline(admin.TabularInline):
    """Edit metrics directly under their parent SocialPlatform."""

    model = PlatformStat
    fields = ("label", "value", "stat_color", "sort_order")
    extra = 1


@admin.register(SocialPlatform)
class SocialPlatformAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "platform_type",
        "username_handle",
        "is_active",
        "sort_order",
    )
    list_editable = ("is_active", "sort_order")
    list_filter = ("platform_type", "is_active")
    search_fields = ("name", "username_handle", "api_identifier")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PlatformStatInline]


@admin.register(PlatformStat)
class PlatformStatAdmin(admin.ModelAdmin):
    list_display = ("platform", "label", "value", "stat_color", "sort_order")
    list_filter = ("platform", "stat_color")
    list_editable = ("value", "stat_color", "sort_order")
    search_fields = ("label", "value")


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at", "ip_address")
    date_hierarchy = "created_at"
    list_editable = ("is_read",)
    ordering = ("-created_at", "is_read")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "email",
                    "subject",
                    "message",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("ip_address", "created_at", "is_read"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Mark selected inquiries as read")
    def mark_as_read(
        self,
        request: HttpRequest,
        queryset: QuerySet[ContactInquiry],
    ) -> None:
        updated: int = queryset.update(is_read=True)
        self.message_user(
            request,
            f"{updated} inquiry/inquiries marked as read.",
        )

    actions: tuple[str, ...] = ("mark_as_read",)