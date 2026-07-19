from django.core.validators import MaxValueValidator, MinValueValidator
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


class Skill(models.Model):
    """An individual technical skill (e.g. 'Python', 'Django').

    Skills are an atomic concept: a single row can belong to many
    ``TechnicalDomain`` rows via the M2M on ``TechnicalDomain.skills``.
    """

    name = models.CharField(
        verbose_name=_("Skill Name"),
        max_length=100,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name=_("URL Slug"),
        max_length=100,
        unique=True,
        blank=True,
    )
    proficiency = models.PositiveSmallIntegerField(
        verbose_name=_("Proficiency %"),
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text=_("Percentage from 1 to 100"),
    )

    class Meta:
        ordering = ["-proficiency", "name"]
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        indexes = [
            models.Index(fields=["-proficiency"]),
        ]

    def __str__(self) -> str:
        return self.name

    LAYER_ORDER: tuple[str, ...] = (
        "languages",
        "frameworks",
        "data",
        "devops",
    )

    LAYER_LABELS: dict[str, str] = {
        "languages": "Languages & Core Syntax",
        "frameworks": "Frameworks & Platforms",
        "data": "Databases & Event Streams",
        "devops": "DevOps & Cloud Infrastructure",
    }

    LAYER_KEYWORDS: dict[str, tuple[str, ...]] = {
        "languages": (
            "python", "javascript", "typescript", "go", "golang", "rust",
            "java", "kotlin", "swift", "c", "c++", "c#", "ruby", "php",
            "scala", "bash", "shell", "sql", "html", "css",
        ),
        "frameworks": (
            "django", "flask", "fastapi", "fast api", "starlette", "express",
            "react", "next.js", "nextjs", "vue", "angular", "svelte",
            "odoo", "openerp", "rails", "laravel", "spring", "odoo.sh",
            "owl",
        ),
        "data": (
            "postgres", "postgresql", "mysql", "mariadb", "sqlite", "redis",
            "mongodb", "cassandra", "kafka", "rabbitmq", "celery",
            "elasticsearch", "dynamodb", "influxdb",
        ),
        "devops": (
            "docker", "kubernetes", "k8s", "helm", "terraform", "ansible",
            "jenkins", "github actions", "gitlab ci", "circleci", "argo",
            "nginx", "apache", "aws", "azure", "gcp", "digitalocean",
            "linux", "ubuntu", "debian", "centos", "prometheus",
            "grafana", "datadog", "ci/cd", "cicd", "loki"
        ),
    }

    LAYER_ICONS: dict[str, str] = {
        "languages": "code",
        "frameworks": "layers",
        "data": "database",
        "devops": "cloud",
    }

    def _normalized_token(self) -> str:
        return (self.slug or self.name or "").strip().lower()

    def _token_matches(self, token: str, keyword: str) -> bool:
        """Match a keyword against the skill token on word boundaries.

        Both ``token`` (the lowercased slug/name) and ``keyword`` are
        normalised on non-alphanumeric separators so phrases such as
        ``"CI/CD"`` or ``"github actions"`` match against slugs like
        ``"ci-cd"`` and ``"github-actions"``. The implementation is
        order-independent at the keyword-token level but requires every
        keyword token to be present in the skill token, which prevents
        ``"go"`` from matching ``"django"`` and ``"c"`` from matching
        ``"docker"``.
        """
        if not token or not keyword:
            return False

        def _split(value: str) -> list[str]:
            normalised = value.replace("-", " ").replace("/", " ")
            return [t for t in normalised.split() if t]

        skill_tokens = _split(token)
        kw_tokens = _split(keyword)
        if not kw_tokens:
            return False
        skill_set = set(skill_tokens)
        return all(t in skill_set for t in kw_tokens)

    def get_layer(self) -> str:
        """Return the technical-stack layer key for this skill.

        The layer is derived non-destructively from the skill's ``slug``
        or ``name`` by matching against known keywords on word
        boundaries. New skills fall back to ``"languages"`` when no
        keyword matches, keeping the helper total and template-safe
        without requiring any schema changes.
        """
        token = self._normalized_token()
        for layer_key in self.LAYER_ORDER:
            keywords = self.LAYER_KEYWORDS.get(layer_key, ())
            for kw in keywords:
                if self._token_matches(token, kw):
                    return layer_key
        return "languages"

    def get_layer_label(self) -> str:
        """Return the human-readable layer name for this skill."""
        return self.LAYER_LABELS.get(self.get_layer(), self.LAYER_LABELS["languages"])

    def get_layer_icon(self) -> str:
        """Return the icon identifier for the layer this skill belongs to."""
        return self.LAYER_ICONS.get(self.get_layer(), self.LAYER_ICONS["languages"])


class TechnicalDomain(models.Model):
    """A grouping of related skills (e.g. 'Backend Architecture')."""

    name = models.CharField(
        verbose_name=_("Domain Name"),
        max_length=100,
        unique=True,
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
    order = models.PositiveSmallIntegerField(
        default=0,
        db_index=True,
        verbose_name=_("Display Order"),
        help_text=_("Lower numbers appear first"),
    )
    skills = models.ManyToManyField(
        Skill,
        related_name="domains",
        blank=True,
        verbose_name=_("Skills"),
        help_text=_("Select all skills that apply to this technical domain."),
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("Technical Domain")
        verbose_name_plural = _("Technical Domains")

    def __str__(self) -> str:
        return self.name


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

    def get_technologies(self):
        """Return the list of technologies used in this role.

        The model intentionally does not declare a technologies relation
        to keep the schema stable; this helper exposes a template-safe
        empty list so the work-experience template can render its
        tech-stack footer unconditionally with ``{% if job.get_technologies %}``
        and only iterate when the relation is wired up in the future.
        """
        related = getattr(self, "technologies", None)
        if related is None:
            return []
        return related.all()


class SocialPlatform(models.Model):
    """A social or coding platform that appears on the Media page."""

    PLATFORM_TYPE_CHOICES: list[tuple[str, "str"]] = [
        ("stat_driven", _("Live Stats Platform (GitHub, LeetCode, etc.)")),
        ("simple_link", _("Simple Profile Link (LinkedIn, X, etc.)")),
    ]

    name = models.CharField(
        verbose_name=_("Platform Name"),
        max_length=100,
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
    )
    profile_url = models.URLField(verbose_name=_("Profile URL"))
    username_handle = models.CharField(
        verbose_name=_("Username / Handle"),
        max_length=100,
    )
    avatar_or_logo = models.ImageField(
        verbose_name=_("Custom Avatar/Logo"),
        upload_to="media_platforms/",
        blank=True,
        null=True,
    )
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("FontAwesome or SVG class/identifier for the platform logo"),
    )
    platform_type = models.CharField(
        max_length=20,
        choices=PLATFORM_TYPE_CHOICES,
        default="simple_link",
        db_index=True,
    )
    api_identifier = models.CharField(
        max_length=50,
        blank=True,
        help_text=_(
            "Identifier used by the background stats fetcher "
            "(e.g., 'github', 'leetcode')"
        ),
    )
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Social Platform")
        verbose_name_plural = _("Social Platforms")
        indexes = [
            models.Index(fields=["is_active", "platform_type", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.name


class PlatformStat(models.Model):
    """A single key/value metric displayed on a stat-driven platform card."""

    STAT_COLOR_CHOICES: list[tuple[str, str]] = [
        ("green", _("Green")),
        ("yellow", _("Yellow")),
        ("red", _("Red")),
        ("blue", _("Blue")),
        ("purple", _("Purple")),
        ("gray", _("Gray")),
    ]

    platform = models.ForeignKey(
        SocialPlatform,
        on_delete=models.CASCADE,
        related_name="stats",
        verbose_name=_("Platform"),
    )
    label = models.CharField(
        verbose_name=_("Metric Label"),
        max_length=50,
    )
    value = models.CharField(
        verbose_name=_("Metric Value"),
        max_length=50,
    )
    stat_color = models.CharField(
        max_length=20,
        choices=STAT_COLOR_CHOICES,
        default="gray",
        verbose_name=_("Accent Color for UI Badge/Progress"),
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label"]
        verbose_name = _("Platform Stat")
        verbose_name_plural = _("Platform Stats")
        indexes = [
            models.Index(fields=["platform", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.platform.name} - {self.label}: {self.value}"
