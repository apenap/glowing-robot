# Sistema Restaurante

Sistema de gestión para restaurantes desarrollado con Flask, que incluye un Punto de Venta (POS), vista de cocina y panel de administración en una sola aplicación.

## Características

- **Punto de Venta (POS):** Toma y gestión de pedidos por mesa, agrupación de productos por categorías, observaciones y tipo de servicio (aquí/llevar).
- **Vista Cocina:** Visualización de comandas pendientes y marcado de pedidos como completados.
- **Panel de Administración:** Gestión de productos, categorías y usuarios. Dashboard con estadísticas de ventas.
- **Roles de usuario:** Acceso diferenciado para meseros, cocina y administradores.
- **Carga de imágenes para productos** y organización por categorías.
- **Base de datos SQLite** con migración automática.
- **Registro de operaciones (logging).**

## Tecnologías Utilizadas

- Python 3
- Flask
- SQLite
- HTML + CSS (PicoCSS)
- JavaScript

## Instalación Rápida

```bash
git clone https://github.com/apenap/sistema_restaurante.git
cd sistema_restaurante
python sistema_restaurante3.71.py
```

### **Si utilizas un dispositivo Android como servidor, asegúrate de utilizar Pydroid 3.**
- Descarga sistema_restaurante3.71.py
- En Teminal de Pydroid 3, instala Flask con:

```bash
pip install Flask
```

- Abre sistema_restaurante3.71.py
- Ejecuta el código.

## Ingreso

Accede a [http://127.0.0.1:5000](http://127.0.0.1:5000) en tu navegador.

Credenciales por defecto:
- admin / adminpass
- cocina / cocinapass
- mesero / meseropass

## Estructura de Carpetas

```
sistema_restaurante/
│
├── sistema_restaurante3.71.py
├── static/
│   └── img/
└── restaurante.db
```

## Contribución

¡Se aceptan sugerencias, donaciones y mejoras! Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para detalles.

## Licencia


