from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Weight, Precio
from .forms import UploadFileForm
from .truncate import truncate_tables
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import plotly.express as px
from decimal import Decimal, ROUND_HALF_UP

def home(request):
    return render(request, 'home.html')

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Truncate existing data and get status messages
            truncate_tables()

            # Process the uploaded file
            excel_file = request.FILES['file']
            xls = pd.ExcelFile(excel_file)

            # Process 'Weight' sheet
            if 'weights' in xls.sheet_names:
                weights_df = pd.read_excel(xls, sheet_name='weights')
                for _, row in weights_df.iterrows():
                    Weight.objects.create(
                        fecha=row['Fecha'],
                        activos=row['activos'],
                        portafolio_1=row['portafolio 1'],
                        portafolio_2=row['portafolio 2'],
                    )

            # Process 'Precios' sheet
            if 'Precios' in xls.sheet_names:
                precios_df = pd.read_excel(xls, sheet_name='Precios')
                for _, row in precios_df.iterrows():
                    Precio.objects.create(
                        dates=row['Dates'],
                        eeuu=row['EEUU'],
                        europa=row['Europa'],
                        japon=row['Japón'],
                        em_asia=row['EM Asia'],
                        latam=row['Latam'],
                        high_yield=row['High Yield'],
                        ig_corporate=row['IG Corporate'],
                        emhc=row['EMHC'],
                        latam_hy=row['Latam HY'],
                        uk=row['UK'],
                        asia_desarrollada=row['Asia Desarrollada'],
                        emea=row['EMEA'],
                        otros_rv=row['Otros RV'],
                        tesoro=row['Tesoro'],
                        mbs_cmbs_ambs=row['MBS+CMBS+AMBS'],
                        abs=row['ABS'],
                        mm_caja=row['MM/Caja'],
                    )

            # Redirect to the same upload page with a query parameter to show the completion modal
            return HttpResponseRedirect(f"{reverse('upload')}?completed=true")
    else:
        form = UploadFileForm()

    # Check if the loading has completed based on the query parameter
    loading_completed = request.GET.get('completed') == 'true'

    return render(request, 'upload.html', {'form': form, 'loading_completed': loading_completed})

def normalize_activo_name(activo_name):
    # Convertir a minúsculas y reemplazar caracteres especiales con guiones bajos
    return activo_name.lower().replace('+', '_').replace('/', '_').replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

def portfolio_view(request):
    portafolio_options = ['portafolio_1', 'portafolio_2']
    selected_portafolio = request.GET.get('portafolio')
    V0 = Decimal(1000000000)  # 1 billón de dólares

    cantidades_iniciales = []

    if selected_portafolio in portafolio_options:
        # Obtener los precios del 15/02/22
        precios_15_feb = Precio.objects.filter(dates='2022-02-15').first()
        
        # Obtener los pesos w_{i,0} del modelo Weight
        pesos = Weight.objects.all()

        for peso in pesos:
            # Normalizar el nombre del activo
            activo_name = normalize_activo_name(peso.activos)
            
            # Obtener el precio del activo en el 15/02/22
            precio_activo = getattr(precios_15_feb, activo_name, None)
            
            if precio_activo:
                # Obtener el peso del activo en el portafolio seleccionado
                portafolio_weight = getattr(peso, selected_portafolio)
                
                # Calcular C_{i,0} usando la fórmula
                cantidad_inicial = (portafolio_weight * V0) / precio_activo

                # Calcular el valor en dólares del activo en el portafolio
                valor_en_dolares = portafolio_weight * V0

                # Añadir los resultados a la lista
                cantidades_iniciales.append({
                    'activo': peso.activos,
                    'cantidad_inicial': cantidad_inicial,
                    'peso_decimal': round(portafolio_weight, 3),
                    'valor_en_dolares': valor_en_dolares
                })
            else:
                print(f"Precio no encontrado para el activo: {peso.activos}")

    context = {
        'portafolio_options': portafolio_options,
        'selected_portafolio': selected_portafolio,
        'cantidades_iniciales': cantidades_iniciales,
    }

    return render(request, 'portfolio.html', context)

def prices_view(request):
    # Fetch all records from the Precios table
    precios_list = Precio.objects.all()

    # Get the selected items per page from the query parameters, default to 10
    items_per_page = request.GET.get('items_per_page', 10)

    # Set up the paginator
    paginator = Paginator(precios_list, items_per_page)
    page = request.GET.get('page', 1)

    try:
        precios = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page.
        precios = paginator.page(1)
    except EmptyPage:
        # If the page is out of range, deliver the last page of results.
        precios = paginator.page(paginator.num_pages)

    context = {
        'precios': precios,
        'items_per_page': items_per_page,
    }

    return render(request, 'prices.html', context)

class ValoresView(APIView):
    def get(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Debe proporcionar fecha_inicio y fecha_fin"}, status=status.HTTP_400_BAD_REQUEST)

        # Filtrar los precios en el rango de fechas proporcionado
        precios = Precio.objects.filter(dates__range=[fecha_inicio, fecha_fin])
        cantidades = Weight.objects.all()

        resultados = []

        for fecha in precios.values('dates').distinct():
            fecha_actual = fecha['dates']
            v_t = 0
            valores = []

            # Calcular x_{i,t} para cada activo en la fecha actual
            for cantidad in cantidades:
                # Asumimos que el campo 'activos' en 'Weight' se corresponde con una de las regiones en 'Precio'
                precio_actual = precios.filter(dates=fecha_actual).first()
                if precio_actual:
                    # Obtener el precio correspondiente al activo
                    precio_activo = getattr(precio_actual, cantidad.activos.lower(), None)
                    if precio_activo is not None:
                        x_it = precio_activo * cantidad.portafolio_1  # Supongo que 'portafolio_1' es c_{i,0}
                        v_t += x_it
                        valores.append({
                            "activo": cantidad.activos,
                            "x_it": x_it,
                            "precio": precio_activo,
                            "cantidad_inicial": cantidad.portafolio_1
                        })

            # Calcular w_{i,t} y preparar el resultado
            for valor in valores:
                w_it = valor['x_it'] / v_t
                valor.update({
                    "w_it": w_it
                })

            resultados.append({
                "fecha": fecha_actual,
                "V_t": v_t,
                "valores": valores,
            })

        return Response(resultados, status=status.HTTP_200_OK)

def calcular_cantidad_iniciales(selected_portafolio):
    V0 = Decimal(1000000000)  # 1 billón de dólares
    cantidades_iniciales = {}

    precios_15_feb = Precio.objects.filter(dates='2022-02-15').first()
    pesos = Weight.objects.all()

    for peso in pesos:
        activo_name = normalize_activo_name(peso.activos)
        precio_activo = getattr(precios_15_feb, activo_name, None)

        if precio_activo:
            # Usar el portafolio seleccionado para obtener el peso adecuado
            portafolio_weight = getattr(peso, selected_portafolio, None)
            if portafolio_weight:
                cantidad_inicial = (portafolio_weight * V0) / precio_activo
                cantidad_inicial = cantidad_inicial.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)  # Redondear a 3 decimales
                cantidades_iniciales[peso.activos] = cantidad_inicial
            else:
                print(f"Peso no encontrado para el activo: {peso.activos} en el portafolio {selected_portafolio}")
        else:
            print(f"Precio no encontrado para el activo: {peso.activos} en la fecha 2022-02-15")

    return cantidades_iniciales

class GraficoDataAPIView(APIView):

    def get(self, request, format=None):
        fecha_inicio = request.GET.get('fecha_inicio', '2022-02-15')
        fecha_fin = request.GET.get('fecha_fin', '2022-02-28')
        selected_portafolio = request.GET.get('portafolio', 'portafolio_1')  # Valor por defecto

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Debe proporcionar fecha_inicio y fecha_fin"}, status=400)

        V0 = Decimal(1000000000)
        precios = Precio.objects.filter(dates__range=[fecha_inicio, fecha_fin])
        cantidades = Weight.objects.all()

        cantidades_iniciales = calcular_cantidad_iniciales(selected_portafolio)

        data = []
        for fecha in precios.values('dates').distinct():
            fecha_actual = fecha['dates']
            v_t = Decimal(0)
            w_vals = {}
            
            for cantidad in cantidades:
                activo_name = normalize_activo_name(cantidad.activos)
                precio_actual = precios.filter(dates=fecha_actual).first()
                
                if precio_actual:
                    precio_activo = getattr(precio_actual, activo_name, None)
                    c_i_0 = cantidades_iniciales.get(cantidad.activos, None)
                    
                    if c_i_0 is not None and precio_activo is not None:
                        x_it = precio_activo * c_i_0
                        x_it = x_it.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)  # Redondear a 3 decimales
                        v_t += x_it
                        w_vals[cantidad.activos] = x_it

            if v_t > 0:
                for activo, x_it in w_vals.items():
                    w_vals[activo] = (x_it / v_t).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)  # Redondear a 3 decimales
            
            data.append({
                "fecha": fecha_actual,
                "V_t": v_t.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP),  # Redondear a 3 decimales
                **w_vals,
            })

        return Response(data)

def graficos_view(request):
    # Obtener parámetros de la solicitud
    fecha_inicio = request.GET.get('fecha_inicio', '2022-02-15')
    fecha_fin = request.GET.get('fecha_fin', '2022-02-16')
    selected_portafolio = request.GET.get('portafolio', 'portafolio_1') 

    # Verificar si las fechas están presentes
    if not fecha_inicio or not fecha_fin:
        return render(request, 'graficos.html', {"error": "Debe proporcionar fecha_inicio y fecha_fin"})

    # Definir las opciones de portafolio
    portafolio_options = ['portafolio_1', 'portafolio_2']  # Asegúrate de que esta lista esté definida

    # Lógica para calcular los datos y gráficos
    V0 = Decimal(1000000000)  # 1 billón de dólares
    precios = Precio.objects.filter(dates__range=[fecha_inicio, fecha_fin])
    cantidades = Weight.objects.all()

    # Calcular o cargar las cantidades iniciales
    cantidades_iniciales = calcular_cantidad_iniciales(selected_portafolio)

    data = []
    for fecha in precios.values('dates').distinct():
        fecha_actual = fecha['dates']
        v_t = 0
        w_vals = {}
        
        for cantidad in cantidades:
            activo_name = normalize_activo_name(cantidad.activos)
            precio_actual = precios.filter(dates=fecha_actual).first()
            
            if precio_actual:
                precio_activo = getattr(precio_actual, activo_name, None)
                c_i_0 = cantidades_iniciales.get(cantidad.activos, None)
                
                if c_i_0 is not None and precio_activo is not None:
                    x_it = precio_activo * c_i_0
                    v_t += x_it
                    w_vals[cantidad.activos] = x_it
                else:
                    if c_i_0 is None:
                        print(f"Cantidad inicial no encontrada para el activo: {cantidad.activos}")
                    if precio_activo is None:
                        print(f"Precio no encontrado para el activo: {cantidad.activos} en la fecha {fecha_actual}")

        if v_t > 0:
            for activo, x_it in w_vals.items():
                w_vals[activo] = x_it / v_t
        
        data.append({
            "fecha": fecha_actual,
            "V_t": v_t,
            **w_vals,
        })

    # Crear gráficos utilizando Plotly
    df = pd.DataFrame(data)
    fig_w = px.area(df, x='fecha', y=[col for col in df.columns if col not in ['fecha', 'V_t']], title='Evolución de w_{i,t}')
    fig_v = px.line(df, x='fecha', y='V_t', title='Evolución de V_t')

    graph_w_html = fig_w.to_html(full_html=False)
    graph_v_html = fig_v.to_html(full_html=False)

    # Pasar todas las variables al contexto del template
    return render(request, 'graficos.html', {
        "graph_w": graph_w_html,
        "graph_v": graph_v_html,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "selected_portafolio": selected_portafolio,
        "portafolio_options": portafolio_options  # Asegúrate de que esto esté aquí
    })
