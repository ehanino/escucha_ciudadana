from django.urls import path
from . import views

urlpatterns = [
    path('', views.bienvenida_view, name='bienvenida'),
    path('diagnostico/', views.index_view, name='index'),
    path('guardar-participacion/', views.guardar_participacion, name='guardar_participacion'),
]
