from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.http import HttpResponse
import csv
from .models import Personero, PerfilUsuario, CentroVotacion, Departamento, Provincia, Distrito


from .forms import CentroVotacionAdminForm, PersoneroAdminForm


# ── Admin: Ubicación (UBIGEO) ──────────────────────────────────────────────────

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('id_ubigeo', 'nombre')
    search_fields = ('nombre', 'id_ubigeo')

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('id_ubigeo', 'nombre', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nombre', 'id_ubigeo')

@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ('id_ubigeo', 'nombre', 'provincia')
    list_filter = ('provincia__departamento', 'provincia')
    search_fields = ('nombre', 'id_ubigeo')


# ── Admin: CentroVotacion ─────────────────────────────────────────────────────

@admin.register(CentroVotacion)
class CentroVotacionAdmin(admin.ModelAdmin):
    form = CentroVotacionAdminForm
    list_display  = ('nombre', 'distrito', 'get_provincia', 'get_departamento', 'direccion', 'total_personeros')
    list_filter   = ('distrito__provincia__departamento', 'distrito__provincia', 'distrito')
    search_fields = ('nombre', 'direccion', 'distrito__nombre')
    ordering      = ('distrito', 'nombre')

    fieldsets = (
        ('Ubicación Geográfica', {
            'fields': ('departamento', 'provincia', 'distrito')
        }),
        ('Información del Centro', {
            'fields': ('nombre', 'direccion')
        }),
    )

    class Media:
        js = ('personeros/js/admin_cascading.js',)

    def get_provincia(self, obj):
        return obj.distrito.provincia if obj.distrito else '-'
    get_provincia.short_description = 'Provincia'

    def get_departamento(self, obj):
        return obj.distrito.provincia.departamento if obj.distrito else '-'
    get_departamento.short_description = 'Departamento'

    def total_personeros(self, obj):
        n = obj.personeros.count()
        color = '#39B54A' if n > 0 else '#94a3b8'
        return format_html(
            '<span style="font-weight:700;color:{}">{} personero(s)</span>',
            color, n
        )
    total_personeros.short_description = 'Personeros asignados'


# ── Admin: Personero ──────────────────────────────────────────────────────────

@admin.register(Personero)
class PersoneroAdmin(admin.ModelAdmin):
    form = PersoneroAdminForm
    list_display  = (
        'nombre_completo', 'dni', 'nro_celular',
        'distrito', 'centro_display', 'numero_mesa', 'cargo',
        'badge_estado', 'perfil_completado'
    )
    list_filter   = ('estado', 'cargo', 'perfil_completado',
                     'distrito__provincia__departamento', 'distrito')
    search_fields = ('apellido_paterno', 'apellido_materno', 'nombres', 'dni',
                     'nro_celular', 'centro_votacion__nombre')
    readonly_fields  = ('fecha_creacion', 'fecha_completado', 'usuario')
    # Eliminamos autocomplete_fields para distrito y centro_votacion porque usaremos el selector en cascada
    # autocomplete_fields = ['centro_votacion', 'distrito'] 
    actions       = ['exportar_csv', 'marcar_confirmado', 'marcar_pendiente']

    class Media:
        js = ('personeros/js/admin_cascading.js',)

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
            'fields': ('centro_votacion', 'numero_mesa', 'cargo'),
        }),
        ('Estado y Gestión', {
            'fields': ('estado', 'observaciones')
        }),
        ('Sistema', {
            'classes': ('collapse',),
            'fields': ('usuario', 'perfil_completado', 'fecha_creacion', 'fecha_completado')
        }),
    )

    # ── Columna personalizada: nombre del centro ──────────────────
    def centro_display(self, obj):
        if obj.centro_votacion:
            nombre = obj.centro_votacion.nombre
            nombre_corto = (nombre[:52] + '...') if len(nombre) > 55 else nombre
            direccion = obj.centro_votacion.direccion or ''
            return format_html(
                '<span title="{}" style="font-size:12px">{}</span>',
                direccion,
                nombre_corto,
            )
        return format_html('<span style="color:#94a3b8;font-size:11px">Sin asignar</span>')
    centro_display.short_description = 'Centro de Votacion'

    # ── Badge estado ──────────────────────────────────────────────
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

    # ── Acciones ──────────────────────────────────────────────────
    def exportar_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="personeros.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Apellido Paterno', 'Apellido Materno', 'Nombres', 'DNI',
            'Fecha Nacimiento', 'Celular', 'Departamento', 'Provincia',
            'Distrito', 'Centro de Votación', 'Dirección Centro', 'Nro Mesa', 'Cargo', 'Estado'
        ])
        for p in queryset:
            centro_nombre  = p.centro_votacion.nombre    if p.centro_votacion else ''
            centro_dir     = p.centro_votacion.direccion if p.centro_votacion else ''
            distrito_nom   = p.distrito.nombre if p.distrito else ''
            provincia_nom  = p.distrito.provincia.nombre if p.distrito else ''
            depto_nom      = p.distrito.provincia.departamento.nombre if p.distrito else ''
            
            writer.writerow([
                p.apellido_paterno, p.apellido_materno, p.nombres, p.dni,
                p.fecha_nacimiento, p.nro_celular,
                depto_nom, provincia_nom, distrito_nom,
                centro_nombre, centro_dir,
                p.numero_mesa, p.get_cargo_display(), p.get_estado_display()
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


# ── Admin: PerfilUsuario ──────────────────────────────────────────────────────

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'rol', 'departamento', 'provincia', 'distrito')
    list_filter   = ('rol', 'departamento')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
