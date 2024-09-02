from django.urls import path
from django.contrib import admin
from .views import home, upload_file, portafolio_view, precios_view

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file, name='upload'),
    path('portafolio/', portafolio_view, name='portafolio'),
    path('precio/', precios_view, name='precios'),
    path('admin/', admin.site.urls),
]
