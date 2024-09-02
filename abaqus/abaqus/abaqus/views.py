from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from .forms import UploadFileForm
from .models import Weight, Precio
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .truncate import truncate_tables
import pandas as pd

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

def portafolio_view(request):
    portafolio_options = ['portafolio_1', 'portafolio_2']
    selected_portafolio = request.GET.get('portafolio')
    starting_value = 1000000000  # Starting value of 1 billion

    data = []
    if selected_portafolio in portafolio_options:
        weight = Weight.objects.all()
        for item in weight:
            portafolio_percentage = getattr(item, selected_portafolio)
            calculated_value = starting_value * portafolio_percentage
            data.append({
                'fecha': item.fecha,
                'activos': item.activos,
                'portafolio': portafolio_percentage,
                'calculated_value': calculated_value,
            })

    context = {
        'portafolio_options': portafolio_options,
        'selected_portafolio': selected_portafolio,
        'data': data,
    }

    return render(request, 'portafolio.html', context)

def precios_view(request):
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

    return render(request, 'precios.html', context)