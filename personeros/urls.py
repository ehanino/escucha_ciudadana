from django.urls import path
from . import views

app_name = 'personeros'

urlpatterns = [
    path('',          views.dashboard_view, name='dashboard'),
    path('login/',    views.login_view,     name='login'),
    path('logout/',   views.logout_view,    name='logout'),
    path('lista/',    views.lista_view,     name='lista'),
    path('mi-perfil/', views.mi_perfil_view, name='mi_perfil'),
    path('api/resumen/', views.api_resumen_view, name='api_resumen'),
]
