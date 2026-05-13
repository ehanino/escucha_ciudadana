# Sistema de Gestión de Personeros — Segunda Vuelta Electoral Perú 2026

> **Contexto:** Se acerca la segunda vuelta de las elecciones presidenciales. Se necesita gestionar
> personeros a nivel nacional de manera eficiente, con datos personales y ubicación de su mesa de sufragio.

---

## Datos ya existentes

| Campo | Tipo | Ejemplo |
|---|---|---|
| Apellido Paterno | Texto | HERRERA |
| Apellido Materno | Texto | GARCÍA |
| Nombres | Texto | JUAN CARLOS |
| DNI | Texto (8 dígitos) | 45123678 |
| Fecha de Nacimiento | Fecha | 15/03/1985 |
| Nro. Celular | Texto | 987654321 |
| Fecha de Creación | Fecha/Hora | 13/05/2026 10:30 |

## Datos adicionales necesarios

| Campo | Tipo | Observación |
|---|---|---|
| Departamento | Texto / FK | 25 departamentos del Perú |
| Provincia | Texto / FK | Depende del departamento |
| Distrito | Texto / FK | Depende de la provincia |
| Colegio Electoral | Texto | Nombre del local de votación |
| Mesa de Sufragio | Texto | Número de mesa |
| Cargo / Rol | Opciones | Personero titular / suplente |
| Estado | Booleano | Confirmado / Pendiente / Retirado |
| Observaciones | Texto libre | Notas del coordinador |

---

## Opciones de Implementación

---

### ✅ Opción A — Módulo nuevo dentro de la app Django existente *(Recomendada)*

**Idea:** Agregar una nueva app `personeros` dentro del proyecto `escucha_ciudadana` ya desplegado en AWS.

**Ventajas:**
- Infraestructura AWS ya lista (EC2 + Nginx + Gunicorn + PostgreSQL)
- No hay que configurar nada nuevo en el servidor
- Admin de Django listo para usar desde el día 1
- Deployment en ~10 minutos (`git pull` + `migrate`)
- Se puede importar la data existente (CSV → Django management command)

**Desventajas:**
- Mezcla dos propósitos en un mismo proyecto (campaña + personeros)
- Si se cae el servidor, ambos sistemas se ven afectados

**Lo que se construiría:**
```
plataforma_personeros/
├── models.py       → Personero, LocalVotacion, Mesa
├── admin.py        → Panel admin con filtros por departamento/provincia/distrito
├── views.py        → CRUD para coordinadores
├── urls.py
└── templates/
    └── personeros/
        ├── lista.html      → Tabla filtrable con buscador
        ├── detalle.html    → Ficha del personero
        └── importar.html   → Subida de CSV masiva
```

**Panel Admin incluiría:**
- Búsqueda por nombre, DNI, distrito
- Filtros por departamento / provincia / estado
- Exportación a CSV
- Importación masiva de datos existentes
- Vista de cobertura: cuántos personeros por mesa/colegio

**Tiempo estimado de desarrollo:** 2–4 horas
**Costo adicional de infraestructura:** $0

---

### 🟡 Opción B — App Django independiente (nuevo proyecto)

**Idea:** Un proyecto Django completamente separado, con su propia base de datos y servidor.

**Ventajas:**
- Totalmente independiente y escalable
- Base de datos propia sin mezclar datos electorales con los de campaña
- Puede tener su propio dominio (ej. `personeros.eduardoherrera.org.pe`)
- Roles de usuario diferenciados (admin nacional, coordinador regional, coordinador provincial)

**Desventajas:**
- Requiere configurar una nueva instancia EC2 o al menos un nuevo servicio en la misma
- Más tiempo de setup inicial
- Implica más costo si se usa EC2 adicional

**Tiempo estimado de desarrollo:** 1–2 días
**Costo adicional:** ~$10–15/mes (EC2 t3.micro adicional) o $0 si se usa la misma instancia

---

### 🟠 Opción C — Solución rápida sin desarrollo: Google Sheets + App Script

**Idea:** Usar Google Sheets como base de datos y Google App Script para automatizaciones.

**Ventajas:**
- Cero tiempo de desarrollo
- Todos en el equipo pueden acceder en tiempo real
- Fácil de compartir con coordinadores regionales
- Google Forms para captura de nuevos personeros

**Desventajas:**
- Sin control de acceso por rol (cualquiera con el link puede editar)
- No escala bien con miles de registros
- No hay validaciones robustas (DNI duplicado, formato, etc.)
- Difícil de auditar cambios
- No apto para datos sensibles sin configurar permisos manualmente

**Tiempo estimado de setup:** 1–2 horas
**Costo:** $0

---

### 🔴 Opción D — Sistema full-stack con dashboard visual (avanzado)

**Idea:** App Django + frontend moderno con mapa de cobertura nacional interactivo.

**Incluiría:**
- Mapa del Perú con cobertura de personeros por departamento (choropleth map)
- Dashboard con indicadores: total personeros, % cobertura por región, mesas sin personero
- Sistema de roles: admin / coordinador departamental / coordinador provincial
- Notificaciones por WhatsApp a personeros (integración con WhatsApp Business API)
- App web responsiva para que coordinadores carguen datos desde celular
- QR de confirmación para cada personero

**Tiempo estimado:** 3–5 días
**Costo adicional:** Igual que Opción B + posible costo de WhatsApp API

---

## Comparativa Rápida

| Criterio | A (Django existente) | B (Django nuevo) | C (Sheets) | D (Full-stack) |
|---|:---:|:---:|:---:|:---:|
| Velocidad de implementación | ⚡⚡⚡ | ⚡⚡ | ⚡⚡⚡⚡ | ⚡ |
| Costo adicional | $0 | $0–15/mes | $0 | $0–15/mes |
| Escalabilidad | Alta | Alta | Baja | Muy Alta |
| Control de acceso | ✅ | ✅ | ❌ | ✅ |
| Importar data CSV | ✅ | ✅ | ✅ | ✅ |
| Exportar a Excel/CSV | ✅ | ✅ | ✅ | ✅ |
| Dashboard visual | Básico | Básico | No | Avanzado |
| Adecuado para segunda vuelta | ✅✅ | ✅ | ✅ | ⚠️ (tiempo) |

---

## Recomendación

> **Dado el tiempo disponible antes de la segunda vuelta, la Opción A es la más estratégica:**
> usa infraestructura ya probada en AWS, permite importar la data existente en horas, y el
> admin de Django ofrece todas las funciones de gestión sin necesidad de construir un frontend
> personalizado. Si se necesita escalar, en el futuro se puede migrar a la Opción B o D.

---

## Próximos pasos (si se elige Opción A)

- [ ] Definir campos exactos del modelo `Personero`
- [ ] Confirmar si se necesitan roles de usuario (coordinador regional vs. admin)
- [ ] Preparar el archivo CSV con la data existente para importar
- [ ] Decidir si se necesita un frontend personalizado o solo el admin de Django
- [ ] Definir dominio/subdominio para el panel de personeros
