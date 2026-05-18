from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from .models import Personero, PerfilUsuario, CentroVotacion, Departamento, Provincia, Distrito
from .forms import PersoneroSelfUpdateForm, PersoneroPublicRegistrationForm


# ── Auth & Registro Público ───────────────────────────────────────────────────

def registro_publico_view(request):
    """Vista pública para que los personeros se registren ellos mismos."""
    if request.method == 'POST':
        form = PersoneroPublicRegistrationForm(request.POST)
        if form.is_valid():
            personero = form.save(commit=False)
            personero.estado = 'pendiente'  # Por defecto queda pendiente de asignación por admin
            personero.save()
            
            # Si el usuario que está registrando ya está autenticado (admin/coordinador),
            # lo redirigimos de vuelta al listado de personeros con un mensaje de éxito.
            if request.user.is_authenticated:
                messages.success(request, f'¡Personero {personero.nombre_completo} registrado exitosamente!')
                return redirect('personeros:lista')
                
            messages.success(request, '¡Gracias por registrarte! Un coordinador se pondrá en contacto contigo pronto para asignarte un local.')
            return render(request, 'personeros/registro_exitoso.html', {'personero': personero})
    else:
        form = PersoneroPublicRegistrationForm()

    # Si es administrador, cargamos el formulario dentro del diseño del panel con menú lateral
    template_name = 'personeros/registro_admin.html' if request.user.is_authenticated else 'personeros/registro_publico.html'
    return render(request, template_name, {'form': form})


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_perfil(user):
    """Retorna el PerfilUsuario o None si no tiene."""
    try:
        return user.perfil
    except PerfilUsuario.DoesNotExist:
        return None


def get_personero_queryset(user):
    """Filtra personeros según el rol del usuario."""
    perfil = get_perfil(user)
    if not perfil or perfil.es_superadmin:
        return Personero.objects.all()
    if perfil.rol == 'coordinador_departamental' and perfil.departamento:
        return Personero.objects.filter(distrito__provincia__departamento=perfil.departamento)
    if perfil.rol == 'coordinador_provincial' and perfil.provincia:
        return Personero.objects.filter(distrito__provincia=perfil.provincia)
    return Personero.objects.none()


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return _redirect_after_login(user)
        messages.error(request, 'DNI o contraseña incorrectos.')

    return render(request, 'personeros/login.html')


def _redirect_after_login(user):
    perfil = get_perfil(user)
    if perfil and perfil.es_personero:
        return redirect('personeros:mi_perfil')
    return redirect('personeros:dashboard')


def logout_view(request):
    logout(request)
    return redirect('bienvenida')


# ── Dashboard (coordinadores / admin) ─────────────────────────────────────────

@login_required(login_url='personeros:login')
def dashboard_view(request):
    perfil = get_perfil(request.user)
    if perfil and perfil.es_personero:
        return redirect('personeros:mi_perfil')

    qs = get_personero_queryset(request.user)

    # KPIs
    total       = qs.count()
    confirmados = qs.filter(estado='confirmado').count()
    pendientes  = qs.filter(estado='pendiente').count()
    retirados   = qs.filter(estado='retirado').count()
    completados = qs.filter(perfil_completado=True).count()

    pct_confirmados = round((confirmados / total * 100) if total else 0)
    pct_completados = round((completados / total * 100) if total else 0)

    # Por departamento
    por_dpto = (
        qs.values('distrito__provincia__departamento__nombre', 'distrito__provincia__departamento__id_ubigeo')
          .annotate(total=Count('id'), confirmados=Count('id', filter=Q(estado='confirmado')))
          .order_by('-total')
    )
    por_dpto_list = [
        {
            'codigo':      d['distrito__provincia__departamento__id_ubigeo'],
            'nombre':      d['distrito__provincia__departamento__nombre'] or 'Sin asignar',
            'total':       d['total'],
            'confirmados': d['confirmados'],
            'pct':         round(d['confirmados'] / d['total'] * 100) if d['total'] else 0,
        }
        for d in por_dpto
    ]

    # Últimos registros
    recientes = qs.order_by('-fecha_creacion')[:10]

    context = {
        'perfil':          perfil,
        'total':           total,
        'confirmados':     confirmados,
        'pendientes':      pendientes,
        'retirados':       retirados,
        'completados':     completados,
        'pct_confirmados': pct_confirmados,
        'pct_completados': pct_completados,
        'por_dpto':        por_dpto_list,
        'recientes':       recientes,
    }
    return render(request, 'personeros/dashboard.html', context)


# ── Lista de personeros ────────────────────────────────────────────────────────

@login_required(login_url='personeros:login')
def lista_view(request):
    perfil = get_perfil(request.user)
    if perfil and perfil.es_personero:
        return redirect('personeros:mi_perfil')

    qs = get_personero_queryset(request.user)

    # Filtros
    q          = request.GET.get('q', '')
    estado     = request.GET.get('estado', '')
    dpto_id    = request.GET.get('departamento', '')

    if q:
        qs = qs.filter(
            Q(nombres__icontains=q) |
            Q(apellido_paterno__icontains=q) |
            Q(apellido_materno__icontains=q) |
            Q(dni__icontains=q) |
            Q(nro_celular__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if dpto_id:
        qs = qs.filter(distrito__provincia__departamento__id_ubigeo=dpto_id)

    context = {
        'perfil':       perfil,
        'personeros':   qs.order_by('apellido_paterno'),
        'departamentos': Departamento.objects.all(),
        'q':            q,
        'estado_sel':   estado,
        'dpto_sel':     dpto_id,
        'total':        qs.count(),
    }
    return render(request, 'personeros/lista.html', context)


# ── Mi Perfil (personero auto-actualización) ──────────────────────────────────

@login_required(login_url='personeros:login')
def mi_perfil_view(request):
    try:
        personero = request.user.personero
    except Personero.DoesNotExist:
        from django.contrib.auth import logout
        logout(request)
        messages.error(request, 'No tienes un perfil de personero asociado.')
        return redirect('personeros:login')

    if request.method == 'POST':
        if personero.perfil_completado:
            messages.warning(request, 'Tu perfil ya fue completado y no puede modificarse.')
            return redirect('personeros:mi_perfil')

        form = PersoneroSelfUpdateForm(request.POST, instance=personero)
        if form.is_valid():
            p = form.save(commit=False)
            p.perfil_completado = True
            p.fecha_completado  = timezone.now()
            p.estado            = 'confirmado'
            p.save()
            messages.success(request, '¡Tus datos fueron guardados exitosamente!')
            return redirect('personeros:mi_perfil')
    else:
        form = PersoneroSelfUpdateForm(instance=personero)

    centro_preasignado = None
    if not personero.perfil_completado and personero.centro_votacion:
        centro_preasignado = personero.centro_votacion

    context = {
        'personero':         personero,
        'form':              form,
        'readonly':          personero.perfil_completado,
        'centro_preasignado': centro_preasignado,
    }
    return render(request, 'personeros/mi_perfil.html', context)


# ── APIs para selectores en cascada ───────────────────────────────────────────

def api_provincias_view(request):
    depto_id = request.GET.get('departamento')
    if not depto_id:
        return JsonResponse({'provincias': []})
    provincias = Provincia.objects.filter(departamento_id=depto_id).values('id_ubigeo', 'nombre')
    return JsonResponse({'provincias': list(provincias)})


def api_distritos_view(request):
    prov_id = request.GET.get('provincia')
    if not prov_id:
        return JsonResponse({'distritos': []})
    distritos = Distrito.objects.filter(provincia_id=prov_id).values('id_ubigeo', 'nombre')
    return JsonResponse({'distritos': list(distritos)})


def api_centros_view(request):
    dist_id = request.GET.get('distrito')
    if not dist_id:
        return JsonResponse({'centros': []})
    centros = CentroVotacion.objects.filter(distrito_id=dist_id).values('id', 'nombre', 'direccion')
    return JsonResponse({'centros': list(centros)})


def api_resumen_view(request):
    qs = get_personero_queryset(request.user)
    por_dpto = (
        qs.values('distrito__provincia__departamento__nombre', 'distrito__provincia__departamento__id_ubigeo')
          .annotate(total=Count('id'), confirmados=Count('id', filter=Q(estado='confirmado')))
    )
    data = [
        {
            'codigo':      d['distrito__provincia__departamento__id_ubigeo'],
            'nombre':      d['distrito__provincia__departamento__nombre'] or 'Sin asignar',
            'total':       d['total'],
            'confirmados': d['confirmados'],
            'pct':         round(d['confirmados'] / d['total'] * 100) if d['total'] else 0,
        }
        for d in por_dpto if d['distrito__provincia__departamento__id_ubigeo']
    ]
    return JsonResponse({'departamentos': data})


@login_required(login_url='personeros:login')
def exportar_excel_view(request):
    perfil = get_perfil(request.user)
    if perfil and perfil.es_personero:
        return redirect('personeros:mi_perfil')

    qs = get_personero_queryset(request.user)

    # Filtros
    q          = request.GET.get('q', '')
    estado     = request.GET.get('estado', '')
    dpto_id    = request.GET.get('departamento', '')

    if q:
        qs = qs.filter(
            Q(nombres__icontains=q) |
            Q(apellido_paterno__icontains=q) |
            Q(apellido_materno__icontains=q) |
            Q(dni__icontains=q) |
            Q(nro_celular__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if dpto_id:
        qs = qs.filter(distrito__provincia__departamento__id_ubigeo=dpto_id)

    # Ordenar por apellido paterno
    qs = qs.order_by('apellido_paterno')

    # Generar la respuesta HTTP del CSV/Excel
    import csv
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"personeros_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Escribir el BOM de UTF-8 para que Excel lo abra con formato correcto
    response.write(b'\xef\xbb\xbf')

    writer = csv.writer(response, delimiter=';') # Punto y coma es el estándar de Excel en español

    # Encabezados
    writer.writerow([
        'DNI',
        'Apellido Paterno',
        'Apellido Materno',
        'Nombres',
        'Celular',
        'Fecha Registro',
        'Departamento',
        'Provincia',
        'Distrito',
        'Centro de Votación',
        'Mesa',
        'Cargo',
        'Estado',
        'Perfil Completado',
        'Fecha Completado',
        'Observaciones'
    ])

    for p in qs:
        # Resolver relaciones de forma segura para evitar AttributeError si hay campos nulos
        dpto = p.distrito.provincia.departamento.nombre if p.distrito and p.distrito.provincia and p.distrito.provincia.departamento else 'Sin asignar'
        prov = p.distrito.provincia.nombre if p.distrito and p.distrito.provincia else 'Sin asignar'
        dist = p.distrito.nombre if p.distrito else 'Sin asignar'
        cv = p.centro_votacion.nombre if p.centro_votacion else 'Sin asignar'

        fecha_reg = timezone.localtime(p.fecha_creacion).strftime('%d/%m/%Y %H:%M:%S') if p.fecha_creacion else ''
        fecha_comp = timezone.localtime(p.fecha_completado).strftime('%d/%m/%Y %H:%M:%S') if p.fecha_completado else ''
        perfil_comp = 'Sí' if p.perfil_completado else 'No'

        writer.writerow([
            p.dni,
            p.apellido_paterno,
            p.apellido_materno,
            p.nombres,
            p.nro_celular,
            fecha_reg,
            dpto,
            prov,
            dist,
            cv,
            p.numero_mesa,
            p.get_cargo_display(),
            p.get_estado_display(),
            perfil_comp,
            fecha_comp,
            p.observaciones
        ])

    return response


def handler404_redirect(request, exception=None):
    """Redirige errores 404 al login, excepto para archivos estáticos."""
    if request.path.startswith(settings.STATIC_URL) or '/static/' in request.path:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound("Archivo estático no encontrado.")
    return redirect('personeros:login')
