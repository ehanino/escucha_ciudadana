# Plan de Acción: Migración de Dominio
## Nuevo Dominio: `juntosporelperu-callao.org.pe`

Este documento detalla los pasos necesarios para migrar la aplicación del sistema de personeros y escucha ciudadana al nuevo dominio adquirido.

---

### 1. Configuración de DNS (Panel del Dominio)
Antes de realizar cambios en el servidor, el dominio debe apuntar a la IP de la instancia de AWS.

- **Registro A**: Crear un registro de tipo `A` que apunte a la IP elástica de tu servidor AWS.
  - Host: `@` (o dejar en blanco)
  - Valor: `[IP_DE_TU_SERVIDOR]`
- **Registro CNAME**: (Opcional) Crear un registro para el subdominio `www`.
  - Host: `www`
  - Valor: `juntosporelperu-callao.org.pe`

---

### 2. Ajustes en Django (`settings.py`)
Aunque actualmente tienes `ALLOWED_HOSTS = ['*']`, es una buena práctica de seguridad especificar los dominios permitidos.

**Modificar `escucha_ciudadana/settings.py`:**
```python
ALLOWED_HOSTS = [
    'juntosporelperu-callao.org.pe',
    'www.juntosporelperu-callao.org.pe',
    'localhost',
    '127.0.0.1'
]

# Si usas HTTPS (recomendado), añade esto para evitar errores de CSRF:
CSRF_TRUSTED_ORIGINS = [
    'https://juntosporelperu-callao.org.pe',
    'https://www.juntosporelperu-callao.org.pe'
]
```

---

### 3. Configuración de Nginx (En el servidor AWS)
Debes actualizar el archivo de configuración de Nginx para que reconozca el nuevo nombre de dominio.

1. Conéctate a tu servidor vía SSH.
2. Edita el archivo de configuración (usualmente en `/etc/nginx/sites-available/`):
   ```bash
   sudo nano /etc/nginx/sites-available/escucha_ciudadana
   ```
3. Cambia la línea `server_name`:
   ```nginx
   server_name juntosporelperu-callao.org.pe www.juntosporelperu-callao.org.pe;
   ```
4. Prueba la configuración y reinicia Nginx:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

### 4. Generación de Certificado SSL (HTTPS)
Para que el sitio sea seguro, utilizaremos Certbot con Let's Encrypt para el nuevo dominio.

1. Ejecuta Certbot para obtener el nuevo certificado:
   ```bash
   sudo certbot --nginx -d juntosporelperu-callao.org.pe -d www.juntosporelperu-callao.org.pe
   ```
2. Sigue las instrucciones en pantalla. Certbot actualizará automáticamente tu archivo de Nginx con las rutas de los certificados.

---

### 5. Redirección del Dominio Antiguo (Opcional)
Si quieres que los usuarios que entren al dominio anterior sean redirigidos automáticamente al nuevo:

Añade un bloque adicional en Nginx:
```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name dominio-antiguo.com;
    return 301 https://juntosporelperu-callao.org.pe$request_uri;
}
```

---

### 6. Verificación Final
- Limpiar caché de Django (si aplica).
- Verificar que el login de personeros funcione correctamente en el nuevo dominio.
- Probar el formulario de registro público (`/personeros/registro/`).
- Verificar que los estilos (CSS) y archivos estáticos carguen sin problemas.

---
> [!IMPORTANT]
> Recuerda que la propagación de DNS puede tardar de 1 a 24 horas, aunque usualmente es rápida (menos de 1 hora).
