from django.urls import path
from django.contrib import admin
from .views import home, upload_file, portfolio_view, prices_view, graphics_view, ValoresView, DataAPIView

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file, name='upload'),
    path('portfolio/', portfolio_view, name='cantidades-iniciales'),
    path('prices/', prices_view, name='precios'),
    path('graphics/', graphics_view, name='graficos'),
    path('admin/', admin.site.urls),
    path('api/data/', DataAPIView.as_view(), name='grafico-data'),
]
