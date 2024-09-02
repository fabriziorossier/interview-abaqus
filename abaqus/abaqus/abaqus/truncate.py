from .models import Weight, Precio

def truncate_tables():
    # Truncate the Weight table
    Weight.objects.all().delete()
    weight_status = "Weight table truncated."
    
    # Truncate the Precio table
    Precio.objects.all().delete()
    precio_status = "Precio table truncated."
    
    return weight_status, precio_status
