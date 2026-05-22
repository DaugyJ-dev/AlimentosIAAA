from django import forms
from .models import CultivoCSV


class CSVUploadForm(forms.ModelForm):

    class Meta:
        model = CultivoCSV
        fields = ['nombre', 'archivo']


class PrediccionForm(forms.Form):

    departamento = forms.CharField(
        max_length=100,
        label='Departamento'
    )

    municipio = forms.CharField(
        max_length=100,
        label='Municipio'
    )

    periodo = forms.CharField(
        max_length=50,
        label='Periodo del año'
    )

    hectareas = forms.FloatField(
        label='Hectáreas disponibles'
    )


class PrediccionForm(forms.Form):
    departamento = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'})
    )
    municipio = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_municipio'})
    )
    periodo = forms.IntegerField(
        initial=2026,
        min_value=2000,
        max_value=2035,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2026'
        })
    )
    hectareas = forms.FloatField(
        min_value=0.1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'min': '0.1',
            'placeholder': 'Ej: 5'
        })
    )

    
    def clean_hectareas(self):
        hectareas = self.cleaned_data['hectareas']
        if hectareas <= 0:
            raise forms.ValidationError('Las hectáreas deben ser mayores a 0.')
        return hectareas

    def clean_anio_siembra(self):
        anio = self.cleaned_data.get('anio_siembra')
        if anio and (anio < 2000 or anio > 2030):
            raise forms.ValidationError('Escribe el año para sembrar')
        return anio