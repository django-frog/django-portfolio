"""
URL configuration for portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf.urls import handler404, handler500
from core import views

urlpatterns = [
    path('', views.HomePageRedirectView.as_view()),
    path('settings/admin/dashboard/', admin.site.urls),
    path('home/', include("core.urls")),
    path('projects/', include("projects.urls")),
] + debug_toolbar_urls()

handler404 = views.Page404View.as_view()
handler500 = views.Page500View.as_view()