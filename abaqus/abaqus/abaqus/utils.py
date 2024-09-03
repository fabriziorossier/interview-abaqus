from decimal import Decimal, ROUND_HALF_UP
from .models import Weight, Precio

def normalize_asset_name(asset_name):
    # Lowercase and replace special characters
    return asset_name.lower().replace('+', '_').replace('/', '_').replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

def calculate_initial_quantities(selected_portafolio):
    V0 = Decimal(1000000000)
    cantidades_iniciales = {}

    precios_15_feb = Precio.objects.filter(dates='2022-02-15').first()
    pesos = Weight.objects.all()

    for peso in pesos:
        activo_name = normalize_asset_name(peso.activos)
        precio_activo = getattr(precios_15_feb, activo_name, None)

        if precio_activo:
            # Use selected portfolio to obtain weight
            portafolio_weight = getattr(peso, selected_portafolio, None)
            if portafolio_weight:
                cantidad_inicial = (portafolio_weight * V0) / precio_activo
                cantidad_inicial = cantidad_inicial.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                cantidades_iniciales[peso.activos] = cantidad_inicial
            else:
                print(f"Peso no encontrado para el activo: {peso.activos} en el portafolio {selected_portafolio}")
        else:
            print(f"Precio no encontrado para el activo: {peso.activos} en la fecha 2022-02-15")

    return cantidades_iniciales