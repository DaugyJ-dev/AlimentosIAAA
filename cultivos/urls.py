from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='inicio'),
    path('cargar-csv/', views.cargar_csv, name='cargar_csv'),
    path('explorar/<int:csv_id>/', views.explorar_datos, name='explorar'),
    path('predecir/<int:csv_id>/', views.predecir, name='predecir'),
    path('resultados/', views.resultados, name='resultados'),
    path('prediccion/<int:csv_id>/', views.prediccion, name='prediccion'),
    path('historial/', views.historial, name='historial'),
]