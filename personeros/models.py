from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

ROLES = [
    ('superadmin', 'Super Administrador'),
    ('coordinador_departamental', 'Coordinador Departamental'),
    ('coordinador_provincial', 'Coordinador Provincial'),
    ('visor', 'Visor (Solo Lectura)'),
    ('personero', 'Personero'),
]


# ── Modelos de Ubicación (UBIGEO) ─────────────────────────────────────────────

class Departamento(models.Model):
    id_ubigeo = models.CharField(max_length=2, primary_key=True, verbose_name='Código UBIGEO')
    nombre    = models.CharField(max_length=100, verbose_name='Nombre')

    class Meta:
        verbose_name        = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering            = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Provincia(models.Model):
    id_ubigeo    = models.CharField(max_length=4, primary_key=True, verbose_name='Código UBIGEO')
    nombre       = models.CharField(max_length=100, verbose_name='Nombre')
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='provincias')

    class Meta:
        verbose_name        = 'Provincia'
        verbose_name_plural = 'Provincias'
        ordering            = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.departamento.nombre})"


class Distrito(models.Model):
    id_ubigeo = models.CharField(max_length=6, primary_key=True, verbose_name='Código UBIGEO')
    nombre    = models.CharField(max_length=100, verbose_name='Nombre')
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='distritos')

    class Meta:
        verbose_name        = 'Distrito'
        verbose_name_plural = 'Distritos'
        ordering            = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.provincia.nombre})"


class CentroVotacion(models.Model):
    """Local de votación importado del padrón ONPE."""
    distrito  = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='centros')
    nombre    = models.CharField(max_length=300, verbose_name='Centro de Votación')
    direccion = models.CharField(max_length=300, blank=True, verbose_name='Dirección')

    class Meta:
        verbose_name        = 'Centro de Votación'
        verbose_name_plural = 'Centros de Votación'
        ordering            = ['distrito', 'nombre']
        unique_together     = ('nombre', 'distrito')

    def __str__(self):
        return f"{self.nombre} — {self.distrito.nombre if self.distrito else 'Sin distrito'}"

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.upper()
        if self.direccion:
            self.direccion = self.direccion.upper()
        super().save(*args, **kwargs)

    @property
    def nombre_con_direccion(self):
        if self.direccion:
            return f"{self.nombre} | {self.direccion}"
        return self.nombre


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
    # Se vincula directamente al distrito para mayor precisión
    distrito = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Distrito')

    # ── Mesa electoral ───────────────────────────────────────────
    centro_votacion   = models.ForeignKey(
        'CentroVotacion', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='personeros',
        verbose_name='Centro de Votación'
    )
    numero_mesa       = models.CharField(max_length=10, blank=True, verbose_name='Nro. de Mesa')
    cargo             = models.CharField(max_length=10, choices=CARGO_CHOICES, default='titular', verbose_name='Cargo')

    # ── Estado y gestión ─────────────────────────────────────────
    estado        = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='confirmado', verbose_name='Estado')
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
    def departamento(self):
        return self.distrito.provincia.departamento if self.distrito else None

    @property
    def provincia(self):
        return self.distrito.provincia if self.distrito else None

    def save(self, *args, **kwargs):
        if self.apellido_paterno:
            self.apellido_paterno = self.apellido_paterno.upper()
        if self.apellido_materno:
            self.apellido_materno = self.apellido_materno.upper()
        if self.nombres:
            self.nombres = self.nombres.upper()
        if self.observaciones:
            self.observaciones = self.observaciones.upper()
        super().save(*args, **kwargs)


class PerfilUsuario(models.Model):
    usuario      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol          = models.CharField(max_length=30, choices=ROLES, default='visor', verbose_name='Rol')
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Departamento asignado')
    provincia    = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Provincia asignada')
    distrito     = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Distrito asignado')

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
