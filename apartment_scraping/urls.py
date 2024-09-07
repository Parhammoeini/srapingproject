"""
URL configuration for apartment_scraping project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path,include
from scraping import views
from django.contrib.auth import views as auth_views

# urls.py


urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.search, name='home'),
    path('terms/', views.terms, name='terms'),
    path('download/', views.download_file, name='download_file'),
    path('', views.custom_login, name='custom_login'),
    path('signup/', views.register, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('scraping/', include('scraping.urls')),
]