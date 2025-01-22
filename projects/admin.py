from django.contrib import admin
from .models import Project, ProjectTag

# Register your models here.
admin.site.register([ProjectTag, Project])