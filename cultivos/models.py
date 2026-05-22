
from django.db import models

class CultivoCSV(models.Model):
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='csv/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class HistorialPrediccion(models.Model):
    csv = models.ForeignKey(CultivoCSV, on_delete=models.CASCADE)
    departamento = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    anio = models.IntegerField()
    hectareas = models.FloatField()
    cultivo_principal = models.CharField(max_length=100)
    rendimiento_principal = models.FloatField()
    nivel_principal = models.CharField(max_length=20)
    produccion_principal = models.FloatField()
    cultivo_alternativo = models.CharField(max_length=100, blank=True, null=True)
    rendimiento_alternativo = models.FloatField(blank=True, null=True)
    nivel_alternativo = models.CharField(max_length=20, blank=True, null=True)
    produccion_alternativa = models.FloatField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.municipio} - {self.cultivo_principal} ({self.anio})"

class PrediccionResultado(models.Model):
    cultivo = models.CharField(max_length=200)
    departamento = models.CharField(max_length=200, blank=True, null=True)
    anio_prediccion = models.IntegerField()
    rendimiento_predicho = models.FloatField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cultivo} - {self.anio_prediccion}"