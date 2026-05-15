# Guía de Despliegue en Producción (AWS)

Este documento detalla los pasos para subir los últimos cambios (Registro Público, Normalización a Mayúsculas, etc.) a tu servidor en AWS.

---

### 1. Preparación Local
Asegúrate de que todos los cambios estén guardados y los archivos de migración creados.
1. Generar migraciones (si no lo has hecho):
   ```bash
   python manage.py makemigrations personeros
   ```
2. Sube tus cambios al repositorio (Git):
   ```bash
   git add .
   git commit -m "Implementación registro público y normalización a mayúsculas"
   git push origin main
   ```

---

### 2. Actualización en el Servidor AWS
Conéctate a tu servidor vía SSH y sigue estos pasos:

1. **Entrar al directorio del proyecto:**
   ```bash
   cd /home/ubuntu/escucha_ciudadana  # Ajusta según tu ruta real
   ```
2. **Descargar los últimos cambios:**
   ```bash
   git pull origin main
   ```
3. **Activar el entorno virtual:**
   ```bash
   source venv/bin/activate
   ```
4. **Instalar nuevas dependencias (si las hay):**
   ```bash
   pip install -r requirements.txt
   ```
5. **Ejecutar migraciones de base de datos:**
   ```bash
   python manage.py migrate
   ```
6. **Recolectar archivos estáticos (CSS, JS, Imágenes):**
   ```bash
   python manage.py collectstatic --noinput
   ```

---

### 3. Reinicio de Servicios
Para que los cambios en el código Python y el nuevo dominio (si ya lo configuraste) surtan efecto:

1. **Reiniciar Gunicorn (o el servidor de apps):**
   ```bash
   sudo systemctl restart gunicorn
   ```
   *(Nota: Si el servicio tiene otro nombre, como `escucha_ciudadana.service`, usa ese).*

2. **Reiniciar Nginx:**
   ```bash
   sudo systemctl restart nginx
   ```

---

### 4. Tareas Post-Despliegue
- **Normalización de Datos Existentes**: Como hemos añadido la función de mayúsculas, los datos antiguos seguirán en minúsculas. Puedes normalizarlos ejecutando este comando una sola vez en el servidor:
  ```bash
  python manage.py shell -c "from personeros.models import Personero; [p.save() for p in Personero.objects.all()]"
  ```
- **Verificación**: Entra al nuevo dominio y prueba registrar un personero de prueba para confirmar que todo fluya correctamente.

---
> [!TIP]
> Si encuentras un error "502 Bad Gateway", verifica los logs de Gunicorn:
> `sudo journalctl -u gunicorn --since "10 minutes ago"`
