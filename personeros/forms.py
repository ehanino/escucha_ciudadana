from django import forms
from .models import Personero, CentroVotacion, Departamento, Provincia, Distrito, ActaElectoral


class PersoneroSelfUpdateForm(forms.ModelForm):
    """Formulario que el personero completa una sola vez con ubicación normalizada."""

    # Campos virtuales para la cascada (no están en el modelo Personero directamente)
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_departamento'})
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        required=False,
        label='Provincia',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_provincia'})
    )

    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        required=False,
        label='Fecha de Nacimiento',
    )

    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.none(),
        required=False,
        label='Distrito',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_distrito'})
    )

    centro_votacion = forms.ModelChoiceField(
        queryset=CentroVotacion.objects.none(),
        required=False,
        empty_label='— Selecciona tu centro de votación —',
        label='Centro de Votación',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_centro_votacion'}),
    )

    class Meta:
        model  = Personero
        fields = [
            'nro_celular',
            'fecha_nacimiento',
            'departamento',
            'provincia',
            'distrito',
            'centro_votacion',
            'numero_mesa',
            'cargo',
        ]
        widgets = {
            'nro_celular':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': '9XXXXXXXX'}),
            'numero_mesa':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 0045'}),
            'cargo':        forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        # Si ya hay datos (ej: vuelta tras error de validación o ya guardado)
        if instance and instance.distrito:
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia=instance.distrito.provincia)
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento=instance.distrito.provincia.departamento)
            self.fields['departamento'].initial = instance.distrito.provincia.departamento
            self.fields['provincia'].initial = instance.distrito.provincia
            self.fields['centro_votacion'].queryset = CentroVotacion.objects.filter(distrito=instance.distrito)

        # Si el POST trae datos de ubicación, poblar los querysets para que la validación pase
        if self.data.get('departamento'):
            try:
                depto_id = self.data.get('departamento')
                self.fields['provincia'].queryset = Provincia.objects.filter(departamento_id=depto_id)
            except (ValueError, TypeError):
                pass
        if self.data.get('provincia'):
            try:
                prov_id = self.data.get('provincia')
                self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=prov_id)
            except (ValueError, TypeError):
                pass
        if self.data.get('distrito'):
            try:
                dist_id = self.data.get('distrito')
                self.fields['centro_votacion'].queryset = CentroVotacion.objects.filter(distrito_id=dist_id)
            except (ValueError, TypeError):
                pass


class CentroVotacionAdminForm(forms.ModelForm):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        widget=forms.Select(attrs={'id': 'id_departamento'})
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        required=False,
        label='Provincia',
        widget=forms.Select(attrs={'id': 'id_provincia'})
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.none(),
        required=True,
        label='Distrito',
        widget=forms.Select(attrs={'id': 'id_distrito'})
    )

    class Meta:
        model = CentroVotacion
        fields = ['departamento', 'provincia', 'distrito', 'nombre', 'direccion', 'actas']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.distrito:
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia=instance.distrito.provincia)
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento=instance.distrito.provincia.departamento)
            self.fields['departamento'].initial = instance.distrito.provincia.departamento
            self.fields['provincia'].initial = instance.distrito.provincia

        if self.data.get('departamento'):
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento_id=self.data.get('departamento'))
        if self.data.get('provincia'):
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=self.data.get('provincia'))


class PersoneroAdminForm(forms.ModelForm):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        widget=forms.Select(attrs={'id': 'id_departamento'})
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        required=False,
        label='Provincia',
        widget=forms.Select(attrs={'id': 'id_provincia'})
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.none(),
        required=False,
        label='Distrito',
        widget=forms.Select(attrs={'id': 'id_distrito'})
    )
    centro_votacion = forms.ModelChoiceField(
        queryset=CentroVotacion.objects.none(),
        required=False,
        label='Centro de Votación',
        widget=forms.Select(attrs={'id': 'id_centro_votacion'})
    )

    class Meta:
        model = Personero
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.distrito:
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia=instance.distrito.provincia)
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento=instance.distrito.provincia.departamento)
            self.fields['departamento'].initial = instance.distrito.provincia.departamento
            self.fields['provincia'].initial = instance.distrito.provincia
            if instance.centro_votacion:
                self.fields['centro_votacion'].queryset = CentroVotacion.objects.filter(distrito=instance.distrito)

        if self.data.get('departamento'):
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento_id=self.data.get('departamento'))
        if self.data.get('provincia'):
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=self.data.get('provincia'))
        if self.data.get('distrito'):
            self.fields['centro_votacion'].queryset = CentroVotacion.objects.filter(distrito_id=self.data.get('distrito'))


class PersoneroPublicRegistrationForm(forms.ModelForm):
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        label='Departamento',
        widget=forms.Select(attrs={'id': 'id_departamento', 'class': 'form-input'})
    )
    provincia = forms.ModelChoiceField(
        queryset=Provincia.objects.none(),
        required=False,
        label='Provincia',
        widget=forms.Select(attrs={'id': 'id_provincia', 'class': 'form-input'})
    )
    distrito = forms.ModelChoiceField(
        queryset=Distrito.objects.none(),
        required=False,
        label='Distrito',
        widget=forms.Select(attrs={'id': 'id_distrito', 'class': 'form-input'})
    )

    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        required=False,
        label='Fecha de Nacimiento',
    )

    nro_celular = forms.CharField(
        required=True,
        label='Nro. Celular',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '9XXXXXXXX'})
    )

    class Meta:
        model = Personero
        fields = [
            'apellido_paterno', 'apellido_materno', 'nombres', 'dni',
            'fecha_nacimiento', 'nro_celular', 'departamento', 'provincia', 'distrito'
        ]
        widgets = {
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apellido Paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Apellido Materno'}),
            'nombres':          forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombres'}),
            'dni':              forms.TextInput(attrs={'class': 'form-input', 'placeholder': '8 dígitos'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get('departamento'):
            self.fields['provincia'].queryset = Provincia.objects.filter(departamento_id=self.data.get('departamento'))
        if self.data.get('provincia'):
            self.fields['distrito'].queryset = Distrito.objects.filter(provincia_id=self.data.get('provincia'))

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if not dni.isdigit() or len(dni) != 8:
            raise forms.ValidationError('El DNI debe tener exactamente 8 dígitos.')
        if Personero.objects.filter(dni=dni).exists():
            raise forms.ValidationError('Este DNI ya está registrado en el sistema.')
        return dni

    def clean_nro_celular(self):
        celular = self.cleaned_data.get('nro_celular', '').strip()
        # Eliminar guiones y espacios en blanco automáticamente
        celular = celular.replace(' ', '').replace('-', '')
        if not celular:
            raise forms.ValidationError('El número de celular es obligatorio.')
        if not celular.isdigit() or len(celular) != 9 or not celular.startswith('9'):
            raise forms.ValidationError('El celular debe empezar con 9 y tener exactamente 9 dígitos.')
        return celular


class ActaElectoralForm(forms.ModelForm):
    class Meta:
        model = ActaElectoral
        fields = ['numero_mesa', 'votos_jp', 'votos_k', 'votos_blanco', 'votos_nulos', 'votos_viciados', 'foto_acta']
        widgets = {
            'numero_mesa':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. 123456', 'style': 'text-align: center; font-size: 18px; font-weight: bold;'}),
            'votos_jp':       forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'inputmode': 'numeric', 'style': 'text-align: center; font-size: 24px; font-weight: bold; color: white;'}),
            'votos_k':        forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'inputmode': 'numeric', 'style': 'text-align: center; font-size: 24px; font-weight: bold; color: white;'}),
            'votos_blanco':   forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'inputmode': 'numeric', 'style': 'text-align: center;'}),
            'votos_nulos':    forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'inputmode': 'numeric', 'style': 'text-align: center;'}),
            'votos_viciados': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'inputmode': 'numeric', 'style': 'text-align: center;'}),
            'foto_acta':      forms.FileInput(attrs={'class': 'form-input', 'id': 'foto_acta_input', 'accept': 'image/*', 'style': 'display: none;'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        v_jp = cleaned_data.get('votos_jp') or 0
        v_k = cleaned_data.get('votos_k') or 0
        v_blanco = cleaned_data.get('votos_blanco') or 0
        v_nulos = cleaned_data.get('votos_nulos') or 0
        v_viciados = cleaned_data.get('votos_viciados') or 0

        total = v_jp + v_k + v_blanco + v_nulos + v_viciados
        if total > 300:
            raise forms.ValidationError(
                f'El total de votos reportado ({total}) supera los 300 electores (límite máximo físico por mesa en Perú).'
            )
        return cleaned_data
