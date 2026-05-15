import csv
import requests
from django.core.management.base import BaseCommand
from personeros.models import Departamento, Provincia, Distrito

class Command(BaseCommand):
    help = 'Puebla las tablas de UBIGEO (Departamento, Provincia, Distrito) desde fuentes oficiales'

    def handle(self, *args, **options):
        # URLs de los CSV (fuente: jmcastagnetto/ubigeo-peru-aumentado)
        URL_DEPTO = "https://raw.githubusercontent.com/jmcastagnetto/ubigeo-peru-aumentado/main/ubigeo_departamento.csv"
        URL_PROV  = "https://raw.githubusercontent.com/jmcastagnetto/ubigeo-peru-aumentado/main/ubigeo_provincia.csv"
        URL_DIST  = "https://raw.githubusercontent.com/jmcastagnetto/ubigeo-peru-aumentado/main/ubigeo_distrito.csv"

        self.stdout.write("Descargando datos de UBIGEO...")

        # 1. Departamentos
        self.stdout.write("Cargando Departamentos...")
        res = requests.get(URL_DEPTO)
        reader = csv.DictReader(res.text.strip().split('\n'))
        for row in reader:
            # En el CSV la columna es 'inei' (6 dígitos, ej: 010000)
            # El ID de depto son los 2 primeros dígitos
            inei = row['inei']
            id_depto = inei[:2]
            Departamento.objects.get_or_create(
                id_ubigeo=id_depto,
                defaults={'nombre': row['departamento'].upper()}
            )

        # 2. Provincias
        self.stdout.write("Cargando Provincias...")
        res = requests.get(URL_PROV)
        reader = csv.DictReader(res.text.strip().split('\n'))
        for row in reader:
            inei = row['inei']
            id_prov = inei[:4]
            id_depto = inei[:2]
            depto = Departamento.objects.get(id_ubigeo=id_depto)
            Provincia.objects.get_or_create(
                id_ubigeo=id_prov,
                defaults={
                    'nombre': row['provincia'].upper(),
                    'departamento': depto
                }
            )

        # 3. Distritos
        self.stdout.write("Cargando Distritos...")
        res = requests.get(URL_DIST)
        # Algunos distritos pueden tener nombres con saltos de línea o comas raras, 
        # pero DictReader suele manejarlo si el CSV está bien formado.
        reader = csv.DictReader(res.text.strip().split('\n'))
        for row in reader:
            inei = row['inei']
            id_dist = inei[:6]
            id_prov = inei[:4]
            try:
                prov = Provincia.objects.get(id_ubigeo=id_prov)
                Distrito.objects.get_or_create(
                    id_ubigeo=id_dist,
                    defaults={
                        'nombre': row['distrito'].upper(),
                        'provincia': prov
                    }
                )
            except Provincia.DoesNotExist:
                self.stderr.write(f"Error: Provincia {id_prov} no encontrada para distrito {id_dist}")

        self.stdout.write(self.style.SUCCESS("¡Población de UBIGEO completada exitosamente!"))
