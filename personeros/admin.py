from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.http import HttpResponse
import csv
from .models import Personero, PerfilUsuario, DEPARTAMENTOS


@admin.register(Personero)
class PersoneroAdmin(admin.ModelAdmin):
    list_display  = (
        'nombre_completo', 'dni', 'nro_celular',
        'departamento', 'provincia', 'distrito',
        'colegio_electoral', 'numero_mesa', 'cargo',
        'badge_estado', 'perfil_completado'
    )
    list_filter   = ('estado', 'cargo', 'departamento', 'perfil_completado')
    search_fields = ('apellido_paterno', 'apellido_materno', 'nombres', 'dni', 'nro_celular')
    readonly_fields = ('fecha_creacion', 'fecha_completado', 'usuario')
    actions       = ['exportar_csv', 'marcar_confirmado', 'marcar_pendiente']

    fieldsets = (
        ('Datos Personales', {
            'fields': (
                ('apellido_paterno', 'apellido_materno'),
                'nombres', 'dni', 'fecha_nacimiento', 'nro_celular',
            )
        }),
        ('Ubicación', {
            'fields': ('departamento', 'provincia', 'distrito')
        }),
        ('Mesa Electoral', {
            'fields': ('colegio_electoral', 'numero_mesa', 'cargo')
        }),
        ('Estado y Gestión', {
            'fields': ('estado', 'observaciones')
        }),
        ('Sistema', {
            'classes': ('collapse',),
            'fields': ('usuario', 'perfil_completado', 'fecha_creacion', 'fecha_completado')
        }),
    )

    def badge_estado(self, obj):
        colores = {
            'confirmado': '#39B54A',
            'pendiente':  '#E8A000',
            'retirado':   '#E31E24',
        }
        color = colores.get(obj.estado, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:bold">{}</span>',
            color, obj.get_estado_display()
        )
    badge_estado.short_description = 'Estado'

    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="personeros.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Apellido Paterno', 'Apellido Materno', 'Nombres', 'DNI',
            'Fecha Nacimiento', 'Celular', 'Departamento', 'Provincia',
            'Distrito', 'Colegio Electoral', 'Nro Mesa', 'Cargo', 'Estado'
        ])
        dptos = dict(DEPARTAMENTOS)
        for p in queryset:
            writer.writerow([
                p.apellido_paterno, p.apellido_materno, p.nombres, p.dni,
                p.fecha_nacimiento, p.nro_celular,
                dptos.get(p.departamento, p.departamento),
                p.provincia, p.distrito,
                p.colegio_electoral, p.numero_mesa,
                p.get_cargo_display(), p.get_estado_display()
            ])
        return response
    exportar_csv.short_description = '📥 Exportar seleccionados a CSV'

    def marcar_confirmado(self, request, queryset):
        updated = queryset.update(estado='confirmado')
        self.message_user(request, f'{updated} personero(s) marcados como Confirmado.')
    marcar_confirmado.short_description = '✅ Marcar como Confirmado'

    def marcar_pendiente(self, request, queryset):
        updated = queryset.update(estado='pendiente')
        self.message_user(request, f'{updated} personero(s) marcados como Pendiente.')
    marcar_pendiente.short_description = '⏳ Marcar como Pendiente'


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'rol', 'departamento', 'provincia')
    list_filter   = ('rol', 'departamento')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
