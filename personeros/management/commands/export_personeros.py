from pathlib import Path
import csv
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from personeros.models import Personero


class Command(BaseCommand):
    help = 'Exporta todos los personeros a CSV (UTF-8 BOM) para abrir en Excel.'

    def add_arguments(self, parser):
        parser.add_argument('--output', '-o', default='personeros_report.csv', help='Ruta de salida relativa a BASE_DIR')
        parser.add_argument('--xlsx', action='store_true', help='Generar XLSX en lugar de CSV (requiere openpyxl)')
        parser.add_argument('--s3', action='store_true', help='Subir el archivo resultante a S3 (requiere boto3 y credenciales)')
        parser.add_argument('--bucket', help='Nombre del bucket S3 (opcional; también se puede leer de env AWS_S3_BUCKET)')
        parser.add_argument('--s3-key', help='Clave/ prefijo en S3 (por defecto exports/<filename>)')

    def handle(self, *args, **options):
        output = options['output']
        base = getattr(settings, 'BASE_DIR', Path(os.getcwd()))
        out_path = Path(base) / output
        out_path.parent.mkdir(parents=True, exist_ok=True)

        qs = Personero.objects.all().select_related('centro_votacion').prefetch_related('actas')

        headers = [
            'nombres', 'apellido_paterno', 'apellido_materno', 'dni', 'nro_celular',
            'colegio', 'fue_personero_centro', 'fue_personero_mesa', 'fecha_creacion', 'estado',
        ]

        # Preparar filas en memoria (suficiente para datasets razonables)
        rows = []
        for p in qs:
            colegio = p.centro_votacion.nombre if p.centro_votacion else ''
            fue_centro = 'SI' if p.cargo == 'Coordinador2' else 'NO'
            fue_mesa = 'SI' if (p.cargo == 'Coordinador3' or p.actas.exists()) else 'NO'
            fecha = p.fecha_creacion.isoformat() if p.fecha_creacion else ''
            rows.append([
                p.nombres, p.apellido_paterno, p.apellido_materno, p.dni, p.nro_celular,
                colegio, fue_centro, fue_mesa, fecha, p.estado,
            ])

        if options.get('xlsx'):
            try:
                from openpyxl import Workbook
            except Exception:
                raise CommandError('openpyxl no está instalado. Instálalo con `pip install openpyxl`')

            # Asegurar extensión .xlsx
            if not str(out_path).lower().endswith('.xlsx'):
                out_path = out_path.with_suffix('.xlsx')

            wb = Workbook()
            ws = wb.active
            ws.append(headers)
            for r in rows:
                ws.append(r)
            wb.save(out_path)
        else:
            # CSV UTF-8 con BOM para abrir en Excel
            with out_path.open('w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for r in rows:
                    writer.writerow(r)
            self.stdout.write(self.style.SUCCESS(f'Exportado {len(rows)} personeros a {out_path}'))

            # Subida opcional a S3
            if options.get('s3'):
                try:
                    import boto3
                    from botocore.exceptions import BotoCoreError, ClientError
                except Exception:
                    raise CommandError('boto3 no está instalado. Instálalo con `pip install boto3`')

                bucket = options.get('bucket') or os.environ.get('AWS_S3_BUCKET')
                if not bucket:
                    raise CommandError('Debe indicar --bucket o configurar AWS_S3_BUCKET en el entorno para subir a S3')

                s3_key = options.get('s3_key')
                if not s3_key:
                    s3_key = f"exports/{out_path.name}"

                s3 = boto3.client('s3')
                try:
                    s3.upload_file(str(out_path), bucket, s3_key)
                except (BotoCoreError, ClientError) as e:
                    raise CommandError(f'Error subiendo a S3: {e}')

                # Construir URL pública asumida (puede variar según configuración de bucket)
                public_url = f'https://{bucket}.s3.amazonaws.com/{s3_key}'
                self.stdout.write(self.style.SUCCESS(f'Subido a S3: {public_url}'))
