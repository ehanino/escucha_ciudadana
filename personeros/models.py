from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

DEPARTAMENTOS = [
    ('AMA', 'Amazonas'), ('ANC', 'Áncash'), ('APU', 'Apurímac'),
    ('ARE', 'Arequipa'), ('AYA', 'Ayacucho'), ('CAJ', 'Cajamarca'),
    ('CAL', 'Callao'), ('CUS', 'Cusco'), ('HUV', 'Huancavelica'),
    ('HUA', 'Huánuco'), ('ICA', 'Ica'), ('JUN', 'Junín'),
    ('LAL', 'La Libertad'), ('LAM', 'Lambayeque'), ('LIM', 'Lima'),
    ('LOR', 'Loreto'), ('MDM', 'Madre de Dios'), ('MOQ', 'Moquegua'),
    ('PAS', 'Pasco'), ('PIU', 'Piura'), ('PUN', 'Puno'),
    ('SAM', 'San Martín'), ('TAC', 'Tacna'), ('TUM', 'Tumbes'),
    ('UCA', 'Ucayali'),
]

ROLES = [
    ('superadmin', 'Super Administrador'),
    ('coordinador_departamental', 'Coordinador Departamental'),
    ('coordinador_provincial', 'Coordinador Provincial'),
    ('visor', 'Visor (Solo Lectura)'),
    ('personero', 'Personero'),
]


class Personero(models.Model):
    CARGO_CHOICES = [
        ('titular', 'Titular'),
        ('suplente', 'Suplente'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('retirado', 'Retirado'),
    ]

    # ── Datos personales ──────────────────────────────────────────
    apellido_paterno = models.CharField(max_length=100, verbose_name='Apellido Paterno')
    apellido_materno = models.CharField(max_length=100, verbose_name='Apellido Materno')
    nombres          = models.CharField(max_length=200, verbose_name='Nombres')
    dni              = models.CharField(max_length=8, unique=True, verbose_name='DNI')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Nacimiento')
    nro_celular      = models.CharField(max_length=20, blank=True, verbose_name='Nro. Celular')
    fecha_creacion   = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    # ── Ubicación ────────────────────────────────────────────────
    departamento = models.CharField(max_length=3, choices=DEPARTAMENTOS, blank=True, verbose_name='Departamento')
    provincia    = models.CharField(max_length=100, blank=True, verbose_name='Provincia')
    distrito     = models.CharField(max_length=100, blank=True, verbose_name='Distrito')

    # ── Mesa electoral ───────────────────────────────────────────
    colegio_electoral = models.CharField(max_length=200, blank=True, verbose_name='Colegio Electoral')
    numero_mesa       = models.CharField(max_length=10, blank=True, verbose_name='Nro. de Mesa')
    cargo             = models.CharField(max_length=10, choices=CARGO_CHOICES, default='titular', verbose_name='Cargo')

    # ── Estado y gestión ─────────────────────────────────────────
    estado        = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    # ── Control de auto-actualización única ──────────────────────
    perfil_completado = models.BooleanField(default=False, verbose_name='Perfil Completado')
    fecha_completado  = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Completado')

    # ── Usuario Django vinculado ──────────────────────────────────
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='personero',
        verbose_name='Usuario del Sistema'
    )

    class Meta:
        verbose_name        = 'Personero'
        verbose_name_plural = 'Personeros'
        ordering            = ['apellido_paterno', 'apellido_materno']

    def __str__(self):
        return f"{self.apellido_paterno} {self.apellido_materno}, {self.nombres} — DNI: {self.dni}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

    @property
    def get_departamento_display_nombre(self):
        return dict(DEPARTAMENTOS).get(self.departamento, self.departamento)


class PerfilUsuario(models.Model):
    usuario      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol          = models.CharField(max_length=30, choices=ROLES, default='visor', verbose_name='Rol')
    departamento = models.CharField(
        max_length=3, choices=DEPARTAMENTOS, blank=True, null=True,
        verbose_name='Departamento asignado',
        help_text='Solo para coordinadores departamentales'
    )
    provincia = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Provincia asignada',
        help_text='Solo para coordinadores provinciales'
    )

    class Meta:
        verbose_name        = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.usuario.username} — {self.get_rol_display()}"

    @property
    def es_superadmin(self):
        return self.rol == 'superadmin'

    @property
    def es_coordinador(self):
        return self.rol in ('coordinador_departamental', 'coordinador_provincial')

    @property
    def es_personero(self):
        return self.rol == 'personero'


# ── Señal: auto-crear usuario Django al registrar un personero ────────────────
@receiver(post_save, sender=Personero)
def crear_usuario_personero(sender, instance, created, **kwargs):
    if created and not instance.usuario:
        user, _ = User.objects.get_or_create(
            username=instance.dni,
            defaults={
                'first_name': instance.nombres,
                'last_name': f"{instance.apellido_paterno} {instance.apellido_materno}",
            }
        )
        user.set_password(instance.dni)
        user.save()

        PerfilUsuario.objects.get_or_create(usuario=user, defaults={'rol': 'personero'})

        # Vincular sin disparar la señal de nuevo
        Personero.objects.filter(pk=instance.pk).update(usuario=user)
        instance.usuario = user
