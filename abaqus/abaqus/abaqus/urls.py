from django.urls import path
from django.contrib import admin
from .views import home, upload_file, cantidades_iniciales_view, precios_view, ValoresView, GraficoDataAPIView, graficos_view

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file, name='upload'),
    path('cantidades-iniciales/', cantidades_iniciales_view, name='cantidades-iniciales'),
    path('precio/', precios_view, name='precios'),
    path('admin/', admin.site.urls),
    path('api/valores/', ValoresView.as_view(), name='valores'),
    path('api/grafico-data/', GraficoDataAPIView.as_view(), name='grafico-data'),
    path('graficos/', graficos_view, name='graficos'),
]
