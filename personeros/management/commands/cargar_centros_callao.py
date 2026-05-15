"""
Management command: cargar_centros_callao
Importa los centros de votacion del Callao desde el CSV de la ONPE, vinculándolos a los nuevos modelos de Distrito.
"""
import csv
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from personeros.models import CentroVotacion, Distrito, Provincia, Departamento


# Distritos cuyos nombres contienen comas en el CSV original,
# causando que se partan en dos columnas al parsear.
DISTRITOS_PARTIDOS = {
    'LA': {
        'PUNTA': 'LA PUNTA',
        'PERLA': 'LA PERLA',
    },
    'CARMEN': {
        'DE': 'CARMEN DE LA LEGUA REYNOSO',
    },
    'MI': {
        'PERU': 'MI PERU',
    },
}


def _limpiar(texto):
    """Elimina espacios extra y normaliza el string."""
    return ' '.join(texto.strip().split())


class Command(BaseCommand):
    help = 'Importa centros de votacion del Callao vinculándolos a modelos Distrito'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina todos los centros existentes antes de importar',
        )
        parser.add_argument(
            '--csv',
            type=str,
            default=None,
            help='Ruta al CSV (por defecto: docs/centro_votacion_Callao_MMT.csv)',
        )

    def handle(self, *args, **options):
        # Ruta del CSV
        csv_path = options['csv'] or os.path.join(
            settings.BASE_DIR, 'docs', 'centro_votacion_Callao_MMT.csv'
        )

        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR('[ERROR] Archivo no encontrado: ' + csv_path))
            return

        # Flush opcional
        if options['flush']:
            eliminados, _ = CentroVotacion.objects.all().delete()
            self.stdout.write(self.style.WARNING('[INFO] ' + str(eliminados) + ' centros eliminados.'))

        creados = 0
        existentes = 0
        errores = 0

        for encoding in ('utf-8-sig', 'latin-1'):
            try:
                with open(csv_path, encoding=encoding, newline='') as f:
                    reader = csv.reader(f)
                    next(reader)  # saltar cabecera

                    for lineno, row in enumerate(reader, start=2):
                        if not any(row):
                            continue

                        try:
                            # region_nom    = _limpiar(row[0]) # CALLAO
                            # provincia_nom = _limpiar(row[1]) # CALLAO
                            distrito_raw  = _limpiar(row[2])
                            centro_raw    = _limpiar(row[3])
                            direccion     = _limpiar(row[4])

                            # Resolver distrito partido por coma en CSV
                            if distrito_raw in DISTRITOS_PARTIDOS:
                                tokens = centro_raw.split()
                                primer_token = tokens[0] if tokens else ''
                                if primer_token in DISTRITOS_PARTIDOS[distrito_raw]:
                                    distrito_nom = DISTRITOS_PARTIDOS[distrito_raw][primer_token]
                                    nombre   = _limpiar(' '.join(tokens[1:]))
                                else:
                                    distrito_nom = distrito_raw
                                    nombre   = centro_raw
                            else:
                                distrito_nom = distrito_raw
                                nombre   = centro_raw

                            if not nombre or not distrito_nom:
                                continue

                            # Buscar el objeto Distrito
                            # Nota: Filtramos por nombre de distrito y provincia 'CALLAO' para asegurar precisión
                            distrito_obj = Distrito.objects.filter(
                                nombre__iexact=distrito_nom,
                                provincia__nombre__iexact='CALLAO'
                            ).first()

                            if not distrito_obj:
                                # Intento B: Solo por nombre si el anterior falla (ej: si se cargó con otro nombre)
                                distrito_obj = Distrito.objects.filter(nombre__iexact=distrito_nom).first()

                            if not distrito_obj:
                                self.stderr.write(self.style.WARNING(f'[WARN] Distrito "{distrito_nom}" no encontrado en la BD UBIGEO.'))
                                errores += 1
                                continue

                            obj, created = CentroVotacion.objects.get_or_create(
                                nombre=nombre,
                                distrito=distrito_obj,
                                defaults={
                                    'direccion': direccion,
                                },
                            )

                            if created:
                                creados += 1
                            else:
                                existentes += 1

                        except Exception as exc:
                            errores += 1
                            self.stderr.write(self.style.WARNING(f'[WARN] Linea {lineno} ignorada: {exc}'))

                break
            except UnicodeDecodeError:
                continue

        self.stdout.write(self.style.SUCCESS(
            f'\nImportacion finalizada:\n'
            f'   Centros creados : {creados}\n'
            f'   Ya existian     : {existentes}\n'
            f'   Errores         : {errores}\n'
            f'   Total en BD     : {CentroVotacion.objects.count()}'
        ))
