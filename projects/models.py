from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Project(models.Model):
    title = models.CharField(verbose_name=_("Title"), max_length=200)
    description = models.CharField(verbose_name=_("Description"),max_length=700)
    start_date = models.DateField(verbose_name=_("Start Date"),default=timezone.now)
    end_date = models.DateField(verbose_name=_("End Date"))
    project_url = models.URLField(verbose_name=_("Project URL"))
    tags = models.ManyToManyField('ProjectTag', verbose_name=_("Tags"))
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def back_up(self):
        self.deleted_at = None
        self.save()

class ProjectTag(models.Model):
    name = models.CharField(verbose_name=_("Name"),max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
