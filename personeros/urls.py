from django.urls import path
from . import views

app_name = 'personeros'

urlpatterns = [
    path('',           views.dashboard_view,   name='dashboard'),
    path('login/',     views.login_view,        name='login'),
    path('logout/',    views.logout_view,       name='logout'),
    path('lista/',     views.lista_view,        name='lista'),
    path('lista/exportar/', views.exportar_excel_view, name='exportar_excel'),
    path('lista/credencial/<int:pk>/', views.descargar_credencial_view, name='descargar_credencial'),
    path('validar/credencial/<uuid:token_uuid>/', views.validar_credencial_publica_view, name='validar_credencial_publica'),
    path('mi-perfil/', views.mi_perfil_view,   name='mi_perfil'),
    path('reportar-escrutinio/', views.reportar_escrutinio_view, name='reportar_escrutinio'),
    path('registro/',  views.registro_publico_view, name='registro_publico'),

    # APIs internas
    path('api/resumen/',    views.api_resumen_view,   name='api_resumen'),
    path('api/provincias/', views.api_provincias_view, name='api_provincias'),
    path('api/distritos/',  views.api_distritos_view,  name='api_distritos'),
    path('api/centros/',    views.api_centros_view,    name='api_centros'),
]
