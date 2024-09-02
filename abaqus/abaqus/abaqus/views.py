from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal, ROUND_HALF_UP
from .models import Weight, Precio
from .forms import UploadFileForm
from rest_framework.views import APIView
from rest_framework.response import Response
import pandas as pd
import plotly.express as px

def home(request):
    return render(request, 'home.html')

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Truncate existing data
            Weight.objects.all().delete()
            Precio.objects.all().delete()

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

def portfolio_view(request):
    portafolio_options = ['portafolio_1', 'portafolio_2']
    selected_portafolio = request.GET.get('portafolio')
    V0 = Decimal(1000000000)

    cantidades_iniciales = []

    if selected_portafolio in portafolio_options:
        # Obtain prices from 2022-02-15
        precios_15_feb = Precio.objects.filter(dates='2022-02-15').first()
        
        # Obtain weights w_{i, 0} from Weight Model
        pesos = Weight.objects.all()

        for peso in pesos:
            # Asset Name Normalize
            activo_name = normalize_activo_name(peso.activos)
            
            # Obtain asset price from 2022-02-15
            precio_activo = getattr(precios_15_feb, activo_name, None)
            
            if precio_activo:
                # Obtain asset weight from selected portfolio
                portafolio_weight = getattr(peso, selected_portafolio)
                
                # Calculate C_{i, 0}
                cantidad_inicial = (portafolio_weight * V0) / precio_activo

                # Calculate asset USD value from selected portfolio
                valor_en_dolares = portafolio_weight * V0

                # Append results to the list
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

def graphics_view(request):
    # Obtain query parameters
    fecha_inicio = request.GET.get('fecha_inicio', '2022-02-15')
    fecha_fin = request.GET.get('fecha_fin', '2022-02-16')
    selected_portafolio = request.GET.get('portafolio', 'portafolio_1') 

    # Verify if dates are present
    if not fecha_inicio or not fecha_fin:
        return render(request, 'graphics.html', {"error": "Must provide Start and End Dates"})

    # Define portfolio options
    portafolio_options = ['portafolio_1', 'portafolio_2']

    # Calculate logic
    V0 = Decimal(1000000000)
    precios = Precio.objects.filter(dates__range=[fecha_inicio, fecha_fin])
    cantidades = Weight.objects.all()

    # Calculate initial quantities
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
                        print(f"Initial quantity not found for asset: {cantidad.activos}")
                    if precio_activo is None:
                        print(f"Price not found for asset: {cantidad.activos} on date {fecha_actual}")

        if v_t > 0:
            for activo, x_it in w_vals.items():
                w_vals[activo] = x_it / v_t
        
        data.append({
            "fecha": fecha_actual,
            "V_t": v_t,
            **w_vals,
        })

    # Create graphics
    df = pd.DataFrame(data)
    fig_w = px.area(df, x='fecha', y=[col for col in df.columns if col not in ['fecha', 'V_t']], title='Evolution of w_{i,t}')
    fig_v = px.line(df, x='fecha', y='V_t', title='Evolution of V_t')

    graph_w_html = fig_w.to_html(full_html=False)
    graph_v_html = fig_v.to_html(full_html=False)

    # Pass variables to template context
    return render(request, 'graphics.html', {
        "graph_w": graph_w_html,
        "graph_v": graph_v_html,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "selected_portafolio": selected_portafolio,
        "portafolio_options": portafolio_options
    })

def normalize_activo_name(activo_name):
    # Lowercase and replace special characters
    return activo_name.lower().replace('+', '_').replace('/', '_').replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

def calcular_cantidad_iniciales(selected_portafolio):
    V0 = Decimal(1000000000)
    cantidades_iniciales = {}

    precios_15_feb = Precio.objects.filter(dates='2022-02-15').first()
    pesos = Weight.objects.all()

    for peso in pesos:
        activo_name = normalize_activo_name(peso.activos)
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

class DataAPIView(APIView):

    def get(self, request, format=None):
        fecha_inicio = request.GET.get('fecha_inicio', '2022-02-15')
        fecha_fin = request.GET.get('fecha_fin', '2022-02-28')
        selected_portafolio = request.GET.get('portafolio', 'portafolio_1')

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Must provide fecha_inicio and fecha_fin"}, status=400)

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
                        x_it = x_it.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                        v_t += x_it
                        w_vals[cantidad.activos] = x_it

            if v_t > 0:
                for activo, x_it in w_vals.items():
                    w_vals[activo] = (x_it / v_t).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            
            data.append({
                "fecha": fecha_actual,
                "V_t": v_t.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP),
                **w_vals,
            })

        return Response(data)