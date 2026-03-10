from django.shortcuts import render
from django.http import JsonResponse
import json
from django.conf import settings
from .models import Tema, Brigadista, Participacion

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def index_view(request):
    # Registrar visita
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ref_code = request.GET.get('ref') or request.session.get('ref_code')
    
    from .models import Visita
    Visita.objects.create(
        ip_direccion=ip,
        user_agent=user_agent,
        ruta=request.path,
        referido_por=ref_code
    )

    temas = Tema.objects.all()
    content_map = {}
    for tema in temas:
        content_map[tema.nombre] = {
            'sabotage': tema.texto_sabotaje,
            'question': tema.pregunta_reflexion,
            'opcion_si': tema.opcion_si,
            'opcion_no': tema.opcion_no,
            'contexto_no': tema.texto_contexto_no,
            'proposal': tema.nombre_propuesta,
            'impact': tema.impacto_detalle
        }
    
    context = {
        'temas': temas,
        'content_json': json.dumps(content_map),
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
    }
    return render(request, 'diagnostico/index.html', context)

def guardar_participacion(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre = data.get('name')
            dni = data.get('dni')
            whatsapp = data.get('phone')
            tema_nombre = data.get('topic')
            tema_libre = data.get('customTopic')
            
            if not all([nombre, whatsapp, tema_nombre]):
                return JsonResponse({'error': 'Faltan datos'}, status=400)
                
            tema = Tema.objects.filter(nombre=tema_nombre).first()
            if not tema:
                return JsonResponse({'error': 'Tema no encontrado'}, status=404)
                
            brigadista = None
            ref_code = request.session.get('ref_code')
            if ref_code:
                brigadista = Brigadista.objects.filter(codigo_referencia=ref_code).first()
                
            Participacion.objects.create(
                nombre_vecino=nombre,
                dni=dni,
                whatsapp=whatsapp,
                tema=tema,
                tema_libre=tema_libre,
                referido_por=brigadista
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)
