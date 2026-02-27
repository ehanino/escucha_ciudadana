from django.db import models

class Tema(models.Model):
    nombre = models.CharField(max_length=100)
    texto_sabotaje = models.TextField()
    pregunta_reflexion = models.TextField()
    opcion_si = models.CharField(max_length=150, default="SÍ, lo vivo a diario")
    opcion_no = models.CharField(max_length=150, default="No sabía que pasaba eso")
    texto_contexto_no = models.TextField(default="Aquí tienes más información sobre lo que está ocurriendo actualmente...", blank=True, null=True)
    nombre_propuesta = models.CharField(max_length=200)
    impacto_detalle = models.TextField()

    def __str__(self):
        return self.nombre

class Brigadista(models.Model):
    nombre = models.CharField(max_length=200)
    codigo_referencia = models.CharField(max_length=50, unique=True)
    zona = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_referencia})"

class Participacion(models.Model):
    nombre_vecino = models.CharField(max_length=200)
    dni = models.CharField(max_length=8, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    referido_por = models.ForeignKey(Brigadista, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_vecino
