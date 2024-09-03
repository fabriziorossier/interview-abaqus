from django.urls import path
from django.contrib import admin
from .views import home, upload_file, portfolio_view, prices_view, graphics_view, transactions_view, DataAPIView, AssetBuyAPIView, AssetSellAPIView

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file, name='upload'),
    path('portfolio/', portfolio_view, name='cantidades-iniciales'),
    path('prices/', prices_view, name='precios'),
    path('graphics/', graphics_view, name='graficos'),
    path('transactions/', transactions_view, name='compra-venta-activos'),
    path('admin/', admin.site.urls),
    path('api/data/', DataAPIView.as_view(), name='grafico-data'),
    path('api/asset-sell/', AssetSellAPIView.as_view(), name='vender-activo'),
    path('api/asset-buy/', AssetBuyAPIView.as_view(), name='comprar-activo'),
]
