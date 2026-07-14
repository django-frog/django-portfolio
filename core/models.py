from django.db import models
from django.utils.translation import gettext_lazy as _
from markdownx.models import MarkdownxField


class ContactInquiry(models.Model):
    """Inbound inquiry submitted through the portfolio contact form."""

    name = models.CharField(
        verbose_name=_("Client Name"),
        max_length=150,
    )
    email = models.EmailField(
        verbose_name=_("Email Address"),
    )
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=200,
    )
    message = models.TextField(
        verbose_name=_("Project Details / Message"),
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_("Sender IP"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(
        verbose_name=_("Read Status"),
        default=False,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at", "is_read"]
        verbose_name = _("Contact Inquiry")
        verbose_name_plural = _("Contact Inquiries")
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_read", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.subject}"


class TechnicalDomain(models.Model):
    """A grouping of related skills (e.g. 'Backend Architecture')."""

    name = models.CharField(
        verbose_name=_("Domain Name"),
        max_length=100,
    )
    description = models.CharField(
        verbose_name=_("Short Description"),
        max_length=300,
        blank=True,
    )
    icon_class = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("FontAwesome or SVG icon class name"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text=_("Lower numbers appear first"),
    )

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Technical Domain")
        verbose_name_plural = _("Technical Domains")

    def __str__(self) -> str:
        return self.name


class Skill(models.Model):
    """An individual technical skill belonging to a domain."""

    domain = models.ForeignKey(
        TechnicalDomain,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name=_("Technical Domain"),
    )
    name = models.CharField(
        verbose_name=_("Skill Name"),
        max_length=100,
    )
    proficiency = models.PositiveSmallIntegerField(
        verbose_name=_("Proficiency %"),
        default=80,
        help_text=_("Percentage from 1 to 100"),
    )
    is_featured = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Show on front page summaries"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
    )

    class Meta:
        ordering = ["sort_order", "-proficiency", "name"]
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        indexes = [
            models.Index(fields=["domain", "sort_order"]),
            models.Index(fields=["is_featured", "-proficiency"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.domain.name})"


class WorkExperience(models.Model):
    """A single role/position held at a company or for a client."""

    company = models.CharField(
        verbose_name=_("Company / Client Name"),
        max_length=150,
    )
    role_title = models.CharField(
        verbose_name=_("Job Title / Role"),
        max_length=150,
    )
    location = models.CharField(
        verbose_name=_("Location or Remote"),
        max_length=100,
        blank=True,
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(
        verbose_name=_("End Date (leave blank if current)"),
        null=True,
        blank=True,
    )
    is_current = models.BooleanField(
        verbose_name=_("Currently Working Here"),
        default=False,
        db_index=True,
    )
    description = MarkdownxField(
        verbose_name=_("Role Description & Achievements (Markdown Supported)"),
    )
    company_url = models.URLField(
        verbose_name=_("Company Website"),
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-is_current", "-start_date"]
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")
        indexes = [
            models.Index(fields=["-is_current", "-start_date"]),
            models.Index(fields=["-start_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.role_title} @ {self.company}"

    def get_duration_display(self) -> str:
        """Return the end-date label, or 'Present' for current roles."""
        if self.is_current:
            return "Present"
        if self.end_date:
            return self.end_date.strftime("%b %Y")
        return ""