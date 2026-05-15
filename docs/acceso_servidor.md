# Guía de Acceso al Servidor AWS

Esta guía detalla cómo conectarte a la instancia de producción y los comandos básicos para el mantenimiento del sistema.

---

### 🔑 1. Conexión vía SSH

Desde tu terminal local (PowerShell en Windows), ejecuta el siguiente comando:

```powershell
ssh -i "C:\Users\ehani\.ssh\llave-campana.pem" ubuntu@3.132.16.193
```

> [!NOTE]
> También puedes conectarte usando el dominio configurado:
> `ssh -i "C:\Users\ehani\.ssh\llave-campana.pem" ubuntu@juntosporelperu-callao.org.pe`

---

### 🚀 2. Flujo de Actualización (Deploy)

Una vez dentro del servidor, sigue estos pasos para subir cambios realizados en desarrollo:

1. **Entrar al directorio:**
   ```bash
   cd /home/ubuntu/escucha_ciudadana
   ```

2. **Activar entorno virtual:**
   ```bash
   source venv/bin/activate
   ```

3. **Descargar cambios:**
   ```bash
   git pull origin main
   ```

4. **Sincronizar Base de Datos y Estáticos:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. **Reiniciar Servicios:**
   ```bash
   sudo systemctl restart gunicorn
   sudo systemctl reload nginx
   ```

---

### 🛠️ 3. Tareas Útiles

#### Ver logs de error (Gunicorn):
```bash
sudo journalctl -u gunicorn --since "10 minutes ago"
```

#### Normalizar datos existentes a Mayúsculas:
```bash
python manage.py shell -c "from personeros.models import Personero; [p.save() for p in Personero.objects.all()]"
```

#### Crear un nuevo Superusuario:
```bash
python manage.py createsuperuser
```

---
> [!IMPORTANT]
> Mantén el archivo `llave-campana.pem` en un lugar seguro y no lo compartas.
