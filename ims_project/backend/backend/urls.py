"""
URL configuration for backend project.

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
from django.urls import path, include
from inventory.views import register_user
from django.shortcuts import redirect  # ✅ Add this import

def redirect_to_api(request):
    return redirect('/api/')  # Change to '/admin/' if you prefer the admin panel

urlpatterns = [
    path("", lambda request: redirect("/api/")),  # ✅ Directly use redirect
    path("admin/", admin.site.urls),
    path("api/", include("inventory.urls")),  # ✅ Ensure no circular import
    path("api/register/", register_user, name="register_user"),
]
