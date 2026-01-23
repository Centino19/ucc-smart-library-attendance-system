from django.contrib import admin
from django.urls import path, include  # <--- Note the 'include' import!

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('library_app.urls')),  # <--- This connects the homepage
]