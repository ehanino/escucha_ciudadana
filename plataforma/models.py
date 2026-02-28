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

class Candidato(models.Model):
    CARGOS_CHOICES = [
        ('diputado', 'Diputado'),
        ('senador_nacional', 'Senador Nacional'),
        ('senador_regional', 'Senador Regional'),
        ('parlamento_andino', 'Parlamento Andino'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Ruta en la URL (ej. eduardo-herrera)")
    cargo = models.CharField(max_length=50, choices=CARGOS_CHOICES, default='diputado')
    ubicacion = models.CharField(max_length=100, default='Callao')
    foto_estatica = models.CharField(max_length=200, default='RetratoSinFondoCamisaBlancaConLogo.png')
    whatsapp_url = models.URLField(blank=True, null=True, default='https://wa.me/51954124774')
    facebook_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.get_cargo_display()}"

class Participacion(models.Model):
    nombre_vecino = models.CharField(max_length=200)
    dni = models.CharField(max_length=8, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    tema_libre = models.CharField(max_length=255, blank=True, null=True, help_text="Especificar tema si se seleccionó 'Otros'")
    candidato = models.ForeignKey(Candidato, on_delete=models.SET_NULL, null=True, blank=True)
    referido_por = models.ForeignKey(Brigadista, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_vecino
