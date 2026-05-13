# Plan de Acción — Sistema Full-Stack de Gestión de Personeros
## Opción D: Dashboard Visual Avanzado

> **Objetivo:** Construir un sistema web completo para gestionar personeros electorales a nivel
> nacional, con mapa de cobertura interactivo, roles de usuario, notificaciones WhatsApp y
> generación de QR. Se integra al proyecto Django existente en AWS.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | Django 6 + Django REST Framework | Ya instalado, en producción en AWS |
| Base de datos | PostgreSQL | Ya en producción |
| Frontend | HTML + Vanilla JS + CSS (sin frameworks) | Liviano, sin build tools |
| Mapa interactivo | Leaflet.js + GeoJSON Perú | Open source, sin costo de API |
| Gráficas | Chart.js | Liviano y muy visual |
| QR Codes | Librería `qrcode` (Python) | Genera PNG/SVG servidor-side |
| WhatsApp | Meta WhatsApp Business API o Twilio | Envío de mensajes masivo |
| Autenticación | Django Auth Groups + roles personalizados | Sin dependencias extra |
| Servidor | AWS EC2 + Nginx + Gunicorn (existente) | Sin cambios de infraestructura |
| Estático | `collectstatic` → Nginx | Ya configurado |

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    AWS EC2 (existente)                  │
│                                                         │
│  Nginx ──► Gunicorn ──► Django                          │
│                          │                              │
│              ┌───────────┴──────────────┐               │
│              │                          │               │
│         App: plataforma           App: personeros (NEW) │
│         (campaña actual)               │                │
│                                   ┌───┴────────────┐   │
│                                   │  API REST      │   │
│                                   │  Dashboard     │   │
│                                   │  Mapa Perú     │   │
│                                   │  QR Generator  │   │
│                                   │  WhatsApp Bot  │   │
│                                   └────────────────┘   │
│                                                         │
│                     PostgreSQL                          │
└─────────────────────────────────────────────────────────┘
```

---

## Roles de Usuario

| Rol | Acceso | Puede hacer |
|---|---|---|
| `superadmin` | Nacional | Todo: crear/editar/borrar, ver dashboards, exportar, enviar WhatsApp |
| `coordinador_departamental` | Su departamento | Ver/editar personeros de su dpto, ver dashboard departamental |
| `coordinador_provincial` | Su provincia | Ver/editar personeros de su provincia |
| `visor` | Solo lectura | Ver listas y estadísticas sin editar |

---

## Modelos de Base de Datos

```python
# personeros/models.py

class Ubigeo(models.Model):
    """Tabla de ubigeo oficial INEI (cargada desde CSV)"""
    codigo      # 6 dígitos (ej. 150101 = Lima > Lima > Lima)
    departamento
    provincia
    distrito

class LocalVotacion(models.Model):
    """Local y mesa de sufragio"""
    ubigeo          → FK(Ubigeo)
    nombre_local    # "I.E. Ricardo Palma"
    direccion
    codigo_local    # Código ONPE

class Mesa(models.Model):
    local           → FK(LocalVotacion)
    numero_mesa     # "0045"
    tiene_personero → BooleanField (computed)

class Personero(models.Model):
    # Datos existentes
    apellido_paterno
    apellido_materno
    nombres
    dni             # Unique, 8 dígitos
    fecha_nacimiento
    nro_celular
    fecha_creacion  # auto_now_add

    # Datos nuevos
    ubigeo_residencia   → FK(Ubigeo)  # donde vive
    mesa                → FK(Mesa)    # donde es personero
    cargo               # titular / suplente
    estado              # confirmado / pendiente / retirado
    observaciones

    # Metadatos
    creado_por      → FK(User)
    fecha_modificacion → auto_now

    # QR y comunicación
    qr_generado     → BooleanField
    whatsapp_enviado → BooleanField
    fecha_envio_wa

class RegistroActividad(models.Model):
    """Auditoría de cambios"""
    personero   → FK(Personero)
    usuario     → FK(User)
    accion      # 'creado' / 'editado' / 'estado_cambiado' / 'qr_generado'
    detalle
    fecha
```

---

## Fases de Implementación

---

### 🔵 FASE 1 — Estructura base y modelos `(Día 1 — ~4 horas)`

**Objetivo:** Django app funcionando con modelos, admin y datos de prueba.

**Tareas:**
- [ ] Crear app Django: `python manage.py startapp personeros`
- [ ] Definir modelos: `Ubigeo`, `LocalVotacion`, `Mesa`, `Personero`, `RegistroActividad`
- [ ] Cargar tabla de ubigeo INEI (CSV con ~1874 distritos del Perú)
- [ ] Crear management command: `importar_personeros` (lee CSV existente)
- [ ] Configurar Admin de Django con filtros avanzados
- [ ] Migraciones y carga inicial de datos
- [ ] Configurar URLs: `/personeros/`

**Archivos creados:**
```
personeros/
├── models.py
├── admin.py
├── apps.py
├── urls.py
├── management/
│   └── commands/
│       ├── importar_ubigeo.py
│       └── importar_personeros.py
└── migrations/
```

**Resultado esperado:** Admin de Django con todos los personeros importados, filtrables por departamento/provincia/distrito.

---

### 🟡 FASE 2 — API REST `(Día 1–2 — ~3 horas)`

**Objetivo:** Endpoints JSON que alimentarán el dashboard y el mapa.

**Endpoints:**

| Método | URL | Descripción |
|---|---|---|
| GET | `/personeros/api/resumen/` | KPIs nacionales (total, confirmados, pendientes) |
| GET | `/personeros/api/por-departamento/` | Conteo agrupado por dpto (para el mapa) |
| GET | `/personeros/api/por-provincia/?dpto=15` | Desglose provincial |
| GET | `/personeros/api/lista/` | Lista paginada con filtros |
| POST | `/personeros/api/crear/` | Crear personero |
| PUT | `/personeros/api/<id>/editar/` | Editar personero |
| POST | `/personeros/api/<id>/generar-qr/` | Generar QR del personero |
| POST | `/personeros/api/<id>/enviar-whatsapp/` | Enviar mensaje WA |
| POST | `/personeros/api/importar-csv/` | Subir CSV masivo |
| GET | `/personeros/api/exportar-excel/` | Descargar Excel filtrado |

**Archivos creados:**
```
personeros/
├── serializers.py
├── api_views.py
└── permissions.py
```

---

### 🟢 FASE 3 — Sistema de autenticación y roles `(Día 2 — ~2 horas)`

**Objetivo:** Login con roles diferenciados. Cada usuario ve solo su ámbito geográfico.

**Tareas:**
- [ ] Crear grupos Django: `superadmin`, `coordinador_departamental`, `coordinador_provincial`, `visor`
- [ ] Modelo `PerfilUsuario` (extiende User): asocia usuario a departamento/provincia
- [ ] Decoradores/mixins de permisos por rol
- [ ] Vista de login personalizada (pantalla de acceso branded)
- [ ] Middleware que filtra QuerySets según rol del usuario logueado

**Archivos creados:**
```
personeros/
├── perfiles.py     # Modelo PerfilUsuario
└── mixins.py       # Mixins de permisos
templates/personeros/
└── login.html
```

---

### 🔵 FASE 4 — Dashboard principal `(Día 2–3 — ~5 horas)`

**Objetivo:** Página web con KPIs y gráficas en tiempo real.

**Secciones del dashboard:**

```
┌─────────────────────────────────────────────────────┐
│  LOGO   Sistema de Personeros — Segunda Vuelta      │
│         [Usuario: Admin Nacional]  [Cerrar sesión]  │
├──────────┬──────────┬──────────┬────────────────────┤
│ TOTAL    │CONFIRMADOS│PENDIENTES│  MESAS SIN         │
│ 1,248    │  987 79% │  231 18% │  PERSONERO: 847    │
├──────────┴──────────┴──────────┴────────────────────┤
│                                                     │
│  [MAPA PERÚ]              [GRÁFICA COBERTURA]       │
│  Cobertura por dpto       % por departamento        │
│  (colores de calor)       (barras horizontales)     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  TABLA: Personeros recientes / Alertas mesas vacías │
│  [Buscar] [Filtrar por dpto] [Exportar Excel]       │
└─────────────────────────────────────────────────────┘
```

**KPIs principales:**
- Total personeros registrados
- % confirmados / pendientes / retirados
- Cobertura por departamento (mesas cubiertas vs. total)
- Mesas sin personero asignado (alerta roja)
- Actividad reciente (últimos registros)

**Tecnologías frontend:**
- `Chart.js` → gráfica de barras de cobertura departamental
- `Leaflet.js` → mapa (se implementa en Fase 5)
- Vanilla JS + `fetch()` → llamadas a la API REST

**Archivos creados:**
```
templates/personeros/
├── base.html           # Layout con sidebar y nav
├── dashboard.html      # Vista principal
├── lista_personeros.html
├── detalle_personero.html
├── formulario_personero.html
└── login.html
static/personeros/
├── css/
│   └── dashboard.css
└── js/
    ├── dashboard.js
    ├── mapa.js
    └── graficas.js
```

---

### 🗺️ FASE 5 — Mapa interactivo del Perú `(Día 3 — ~3 horas)`

**Objetivo:** Mapa de calor (choropleth) que muestra cobertura de personeros por departamento y permite hacer drill-down a provincias/distritos.

**Comportamiento:**
1. Mapa carga con los 25 departamentos coloreados según % de cobertura:
   - 🟢 Verde: ≥ 80% de mesas cubiertas
   - 🟡 Amarillo: 50–79%
   - 🔴 Rojo: < 50%
2. Al hacer clic en un departamento → zoom a provincias del dpto
3. Al hacer clic en una provincia → lista de personeros de esa provincia
4. Tooltip al pasar el mouse → nombre, total personeros, % cobertura

**Datos GeoJSON:**
- Usar GeoJSON oficial del INEI/IGN con límites de departamentos y provincias del Perú
- Fuente pública: `github.com/juaneladio/peru-geojson`

**Archivos creados:**
```
static/personeros/
└── geojson/
    ├── departamentos.geojson
    └── provincias.geojson
```

---

### 📱 FASE 6 — QR y WhatsApp `(Día 4 — ~4 horas)`

**Objetivo:** Generar credencial QR por personero y enviar notificaciones WhatsApp.

#### QR de Personero
Cada personero tendrá un QR que contiene:
```
{
  "id": 123,
  "nombre": "Juan Carlos Herrera García",
  "dni": "45123678",
  "mesa": "0045",
  "local": "I.E. Ricardo Palma",
  "distrito": "Callao",
  "cargo": "titular"
}
```

**Salida:** Imagen PNG + PDF descargable con diseño de credencial.

```
┌──────────────────────────────┐
│  PERSONERO ELECTORAL 2026    │
│  Segunda Vuelta              │
│                              │
│  JUAN CARLOS HERRERA GARCÍA  │
│  DNI: 45123678               │
│  Mesa: 0045 — Titular        │
│  Local: I.E. Ricardo Palma   │
│  Callao, Callao, Callao      │
│                              │
│         [■■ QR ■■]           │
└──────────────────────────────┘
```

**Librerías Python:**
- `qrcode[pil]` → genera QR como imagen
- `reportlab` o `weasyprint` → genera PDF de la credencial

#### Notificaciones WhatsApp
- **Proveedor recomendado:** Meta WhatsApp Business API (via `requests` HTTP)  
  *Alternativa:* Twilio WhatsApp API (más fácil de integrar)
- **Mensajes a enviar:**
  - ✅ Confirmación de registro (automático al guardar)
  - 📋 Recordatorio con datos de mesa (D-3 antes de la elección)
  - 🔔 Recordatorio el día de la elección (6 AM)

**Template de mensaje:**
```
Hola *{nombre}*,

Estás registrado como personero electoral para la Segunda Vuelta.

📍 *Tu mesa asignada:*
• Mesa N°: {numero_mesa}
• Local: {nombre_local}
• Dirección: {direccion}
• Cargo: {cargo}

Tu código QR de credencial está disponible en:
{link_qr}

¡Gracias por tu compromiso! 🇵🇪
```

**Archivos creados:**
```
personeros/
├── qr_generator.py
├── pdf_generator.py
└── whatsapp_service.py
```

---

### 🚀 FASE 7 — Deploy en AWS `(Día 4–5 — ~2 horas)`

**Objetivo:** Poner en producción sin afectar la app de campaña existente.

**Pasos en el servidor:**
```bash
# 1. Actualizar código
cd /var/www/escucha_ciudadana
git pull origin main

# 2. Instalar nuevas dependencias
pip install djangorestframework qrcode[pil] reportlab openpyxl

# 3. Ejecutar migraciones
python manage.py migrate

# 4. Cargar datos de ubigeo
python manage.py importar_ubigeo

# 5. Importar personeros existentes
python manage.py importar_personeros --archivo=/ruta/personeros.csv

# 6. Colectar archivos estáticos
python manage.py collectstatic --noinput

# 7. Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

**Configuración Nginx** (agregar location):
```nginx
location /personeros/ {
    proxy_pass http://unix:/run/gunicorn.sock;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**URL de acceso:** `https://diputado4.eduardoherrera.org.pe/personeros/`  
*(o configurar subdominio: `personeros.eduardoherrera.org.pe`)*

---

## Dependencias Python a instalar

```
djangorestframework==3.16.0   # API REST
qrcode[pil]==8.1.0            # Generación de QR
reportlab==4.4.1              # Generación de PDF
openpyxl==3.1.5               # Exportar a Excel
Pillow==11.2.1                # Procesamiento de imágenes
requests==2.32.5              # Llamadas a WhatsApp API (ya instalado)
```

---

## Cronograma Estimado

| Día | Fases | Entregable |
|---|---|---|
| **Día 1 (mañana)** | Fase 1 + Fase 2 | Modelos listos, data importada, API funcionando |
| **Día 2** | Fase 3 + Fase 4 (inicio) | Login con roles, dashboard KPIs sin mapa |
| **Día 3** | Fase 4 (fin) + Fase 5 | Dashboard completo + mapa interactivo |
| **Día 4** | Fase 6 | QR + WhatsApp integrado |
| **Día 5** | Fase 7 | En producción en AWS |

**Total estimado: 4–5 días de desarrollo**

---

## Costos Estimados

| Ítem | Costo mensual |
|---|---|
| AWS EC2 (ya existente) | $0 adicional |
| Twilio WhatsApp (alternativa) | ~$0.005 por mensaje |
| Meta WhatsApp Business API | Gratis hasta 1,000 conv./mes |
| GeoJSON del Perú | $0 (open source) |
| **Total infraestructura adicional** | **$0 – $5/mes** |

---

## Prerequisitos antes de empezar

- [ ] Confirmar archivo CSV con data existente de personeros (campos exactos)
- [ ] Decidir proveedor de WhatsApp: **Meta API** (gratuito, más complejo) o **Twilio** (pago, más simple)
- [ ] Definir si se usa el mismo dominio (`/personeros/`) o subdominio propio
- [ ] Acceso SSH al servidor AWS para el deploy final
- [ ] Número de WhatsApp Business registrado para envíos

---

## Próximo paso

Con tu aprobación, **empezamos por la Fase 1**: crear la app `personeros`, definir los
modelos y preparar el comando de importación del CSV existente.
¿Tienes disponible el CSV con la data actual para diseñar la importación exacta?
