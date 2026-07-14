from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from markdownx.models import MarkdownxField


class ProjectTag(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Project Tag")
        verbose_name_plural = _("Project Tags")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=200)
    short_description = models.CharField(
        verbose_name=_("Short Description"),
        max_length=300,
    )
    content = MarkdownxField(
        verbose_name=_("Full Case Study & Documentation"),
    )
    slug = models.SlugField(
        verbose_name=_("URL Slug"),
        max_length=250,
        unique=True,
        db_index=True,
        allow_unicode=True,
    )
    start_date = models.DateField(
        verbose_name=_("Start Date"),
        default=timezone.now,
    )
    end_date = models.DateField(
        verbose_name=_("End Date"),
        blank=True,
        null=True,
    )
    project_url = models.URLField(
        verbose_name=_("Project URL"),
        blank=True,
        null=True,
    )
    repository_url = models.URLField(
        verbose_name=_("Repository URL"),
        blank=True,
        null=True,
    )
    live_demo_url = models.URLField(
        verbose_name=_("Live Demo URL"),
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(
        ProjectTag,
        verbose_name=_("Tags"),
        blank=True,
        related_name="projects",
    )
    thumbnail = models.ImageField(
        verbose_name=_("Thumbnail"),
        upload_to="projects/thumbnails/",
        blank=True,
        null=True,
    )
    is_featured = models.BooleanField(
        verbose_name=_("Featured Project"),
        default=False,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["deleted_at"]),
        ]
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def __str__(self) -> str:
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.slug:
            base_slug: str = slugify(self.title, allow_unicode=True) or "project"
            slug: str = base_slug
            counter: int = 1
            while (
                Project.objects.filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("projects:project_detail", kwargs={"slug": self.slug})

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save()

    def back_up(self) -> None:
        self.deleted_at = None
        self.save()