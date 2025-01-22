from django.db import models
from django.utils import timezone

# Create your models here.
class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=700)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    project_url = models.URLField()
    tags = models.ManyToManyField('ProjectTag')
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
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
