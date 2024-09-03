from decimal import Decimal
from .models import Weight, Precio
from .utils import normalize_asset_name

class PortafolioService:

    @staticmethod
    def process_buy(portafolio, activo, monto, fecha):
        # Obtain price of the asset in the given date
        precios = Precio.objects.filter(dates=fecha).first()
        if not precios:
            raise ValueError(f"Price not found for date {fecha}")
        
        # Normalize asset name to correctly find the right price
        activo_name = normalize_asset_name(activo)
        precio_activo = getattr(precios, activo_name, None)

        if not precio_activo:
            raise ValueError(f"Price not found for asset {activo} on date {fecha}.")

        # Obtain asset weight in the portfolio
        peso = Weight.objects.filter(activos=activo).first()
        portafolio_weight = getattr(peso, portafolio)

        # Calculate quantity units to buy
        cantidad_a_comprar = Decimal(monto) / precio_activo

        # Increase asset quantity in the portfolio
        nueva_cantidad = portafolio_weight + cantidad_a_comprar
        setattr(peso, portafolio, nueva_cantidad)
        peso.save()

    @staticmethod
    def process_sell(portafolio, activo, monto, fecha):
        # Obtain price of the asset in the given date
        precios = Precio.objects.filter(dates=fecha).first()
        if not precios:
            raise ValueError(f"Price not found for date {fecha}")
        
        # Normalize asset name to correctly find the right price
        activo_name = normalize_asset_name(activo)
        precio_activo = getattr(precios, activo_name, None)

        if not precio_activo:
            raise ValueError(f"Price not found for asset {activo} on date {fecha}.")

        # Obtain asset weight in the portfolio
        peso = Weight.objects.filter(activos=activo).first()
        portafolio_weight = getattr(peso, portafolio)

        # Calculate quantity units to sell
        cantidad_a_vender = Decimal(monto) / precio_activo

        # Verificar si la cantidad a vender es menor o igual a la cantidad disponible
        if cantidad_a_vender > portafolio_weight:
            raise ValueError(f"No hay suficiente cantidad de {activo} para vender.")

        # Decrease asset quantity in the portfolio
        nueva_cantidad = portafolio_weight - cantidad_a_vender
        setattr(peso, portafolio, nueva_cantidad)
        peso.save()