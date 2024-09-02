from django.db import models

class Weight(models.Model):
    fecha = models.DateField()
    activos = models.CharField(max_length=255)
    portafolio_1 = models.DecimalField(max_digits=10, decimal_places=3)
    portafolio_2 = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.fecha} - {self.activos}"

class Precio(models.Model):
    dates = models.DateField()
    eeuu = models.DecimalField(max_digits=10, decimal_places=4)
    europa = models.DecimalField(max_digits=10, decimal_places=4)
    japon = models.DecimalField(max_digits=10, decimal_places=4)
    em_asia = models.DecimalField(max_digits=10, decimal_places=4)
    latam = models.DecimalField(max_digits=10, decimal_places=4)
    high_yield = models.DecimalField(max_digits=10, decimal_places=4)
    ig_corporate = models.DecimalField(max_digits=10, decimal_places=4)
    emhc = models.DecimalField(max_digits=10, decimal_places=4)
    latam_hy = models.DecimalField(max_digits=10, decimal_places=4)
    uk = models.DecimalField(max_digits=10, decimal_places=4)
    asia_desarrollada = models.DecimalField(max_digits=10, decimal_places=4)
    emea = models.DecimalField(max_digits=10, decimal_places=4)
    otros_rv = models.DecimalField(max_digits=10, decimal_places=4)
    tesoro = models.DecimalField(max_digits=10, decimal_places=4)
    mbs_cmbs_ambs = models.DecimalField(max_digits=10, decimal_places=4)
    abs = models.DecimalField(max_digits=10, decimal_places=4)
    mm_caja = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return f"{self.dates} - {self.eeuu}"

