from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
import csv
from .models import Tema, Brigadista, Participacion

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_propuesta')
    search_fields = ('nombre',)

@admin.register(Brigadista)
class BrigadistaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_referencia', 'zona', 'activo', 'referidos_count')
    search_fields = ('nombre', 'codigo_referencia')
    list_filter = ('activo', 'zona')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _referidos_count=Count('participacion')
        )

    def referidos_count(self, obj):
        return obj._referidos_count
    referidos_count.short_description = 'Nº Vecinos Referidos'
    referidos_count.admin_order_field = '_referidos_count'


@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    list_display = ('nombre_vecino', 'whatsapp', 'tema', 'referido_por', 'fecha_creacion')
    list_filter = ('tema', 'fecha_creacion')
    search_fields = ('nombre_vecino', 'whatsapp')
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "Exportar Seleccionados a CSV"
