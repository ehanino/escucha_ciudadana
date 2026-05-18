# Guía de Comandos Docker para Recarga de Backend y Frontend

Esta guía detalla los comandos de Docker y Docker Compose necesarios para recargar, reconstruir y reiniciar los contenedores de **Backend** y **Frontend** ante cualquier cambio en el código fuente o en las dependencias.

---

## 🔄 1. Recarga Rápida (Sin reconstruir)

Si el entorno de desarrollo tiene **volúmenes montados** (hot-reload activado) y el código no se actualiza automáticamente, o si el proceso interno se congeló, puedes reiniciar los contenedores específicos rápidamente.

### Reiniciar solo el Backend
```bash
docker compose restart backend
```

### Reiniciar solo el Frontend
```bash
docker compose restart frontend
```

### Reiniciar ambos servicios
```bash
docker compose restart backend frontend
```

---

## 🛠️ 2. Reconstrucción por Cambios de Dependencias

Cuando agregas una nueva librería en el backend (ej. en `requirements.txt` o `Pipfile`) o en el frontend (ej. `package.json`), el contenedor **debe ser reconstruido** para instalar las nuevas dependencias.

### Reconstruir e iniciar un contenedor específico (Recomendado)
Este comando reconstruye únicamente el servicio modificado y lo levanta sin afectar a los demás:
```bash
# Para el Backend:
docker compose up -d --build backend

# Para el Frontend:
docker compose up -d --build frontend
```

### Reconstruir todo desde cero (Fuerza bruta)
Si hay cambios estructurales grandes en Dockerfiles o configuraciones de red:
```bash
# 1. Apagar y limpiar contenedores y volúmenes huérfanos
docker compose down

# 2. Levantar todo reconstruyendo las imágenes
docker compose up -d --build
```

---

## 📊 3. Inspección y Logs (Monitoreo de Cambios)

Para comprobar si la recarga automática o la instalación de dependencias falló, es crucial auditar los logs en tiempo real.

### Ver logs en vivo del Backend
```bash
docker compose logs -f --tail=100 backend
```

### Ver logs en vivo del Frontend
```bash
docker compose logs -f --tail=100 frontend
```

---

## 🧹 4. Mantenimiento y Limpieza de Caché

A veces Docker almacena en caché capas antiguas de compilación y no detecta cambios en las dependencias. Usa estos comandos para forzar una limpieza:

### Limpiar caché de construcción de Docker
```bash
docker builder prune -f
```

### Eliminar contenedores parados y recursos huérfanos
```bash
docker system prune -a --volumes
```

---

> [!TIP]
> **Flujo rápido recomendado ante cambios cotidianos:**
> 1. Si cambiaste **código (.py, .js, .html)**: El Hot-Reload debería encargarse. Si falla, ejecuta `docker compose restart [servicio]`.
> 2. Si instalaste **nuevas librerías / dependencias**: Ejecuta `docker compose up -d --build [servicio]`.
