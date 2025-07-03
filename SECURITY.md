# Seguridad

Algunos puntos importantes para desplegar el sistema en producción:

---

## 1. Contraseñas

- Actualmente las contraseñas se guardan en texto plano. Se recomienda cambiar el código para almacenar hashes de contraseñas usando `werkzeug.security` o similar antes de uso real.

## 2. Clave secreta

- Cambia la clave secreta (`app.secret_key`) por una variable de entorno segura en producción.

## 3. Cookies de sesión

- Configura los parámetros de seguridad para cookies de sesión en Flask:
  - `SESSION_COOKIE_SECURE = True`
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`

## 4. Subida de archivos

- El sistema sólo permite archivos de imagen (`png`, `jpg`, `jpeg`, `gif`).
- Considera renombrar archivos subidos con UUIDs para evitar conflictos de nombres.

## 5. Acceso por roles

- Todas las rutas sensibles requieren autenticación y el rol adecuado.
- Si el usuario no tiene permisos, es redirigido al login.

## 6. Despliegue

- Nunca uses `debug=True` en producción.
- Usa un servidor de aplicaciones (Gunicorn, uWSGI) detrás de un proxy (Nginx, Apache) para servir la app.

## 7. SQLite

- SQLite es ideal para desarrollo o pequeños negocios. Para mayor concurrencia o robustez, considerar PostgreSQL o MySQL.
