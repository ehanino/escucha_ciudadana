from django import forms
from .models import Personero, DEPARTAMENTOS


class PersoneroSelfUpdateForm(forms.ModelForm):
    """Formulario que el personero completa una sola vez."""

    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        required=False,
        label='Fecha de Nacimiento'
    )

    class Meta:
        model  = Personero
        fields = [
            'nro_celular',
            'fecha_nacimiento',
            'departamento',
            'provincia',
            'distrito',
            'colegio_electoral',
            'numero_mesa',
            'cargo',
        ]
        widgets = {
            'nro_celular':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': '9XXXXXXXX'}),
            'departamento':       forms.Select(attrs={'class': 'form-input'}),
            'provincia':          forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Lima'}),
            'distrito':           forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Miraflores'}),
            'colegio_electoral':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre del colegio electoral'}),
            'numero_mesa':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 0045'}),
            'cargo':              forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'nro_celular':       'Número de Celular',
            'departamento':      'Departamento',
            'provincia':         'Provincia',
            'distrito':          'Distrito',
            'colegio_electoral': 'Colegio Electoral',
            'numero_mesa':       'Número de Mesa',
            'cargo':             'Cargo',
        }
