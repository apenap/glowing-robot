# Esquema de Base de Datos

La base de datos utiliza SQLite. Estas son las principales tablas y sus campos:

---

## 1. categorias

| Campo   | Tipo    | Descripción                |
|---------|---------|----------------------------|
| id      | INTEGER | Clave primaria             |
| nombre  | TEXT    | Nombre único de categoría  |

---

## 2. usuarios

| Campo    | Tipo    | Descripción          |
|----------|---------|----------------------|
| id       | INTEGER | Clave primaria       |
| username | TEXT    | Nombre de usuario    |
| password | TEXT    | Contraseña           |
| rol      | TEXT    | Rol (admin/cocina/mesero) |

---

## 3. productos

| Campo        | Tipo    | Descripción                                  |
|--------------|---------|----------------------------------------------|
| id           | INTEGER | Clave primaria                               |
| nombre       | TEXT    | Nombre único de producto                     |
| precio       | REAL    | Precio del producto                          |
| imagen       | TEXT    | Nombre de archivo de imagen                  |
| categoria_id | INTEGER | FK a categorias(id)                          |

---

## 4. comandas

| Campo         | Tipo    | Descripción                                  |
|---------------|---------|----------------------------------------------|
| id            | INTEGER | Clave primaria                               |
| mesa          | TEXT    | Número o nombre de mesa                      |
| producto      | TEXT    | Nombre del producto                          |
| precio        | REAL    | Precio unitario                              |
| cantidad      | INTEGER | Cantidad pedida                              |
| fecha         | TEXT    | Fecha/hora del pedido                        |
| estado        | TEXT    | Estado (pendiente/completado)                |
| tipo_servicio | TEXT    | Aquí / Llevar                                |
| observaciones | TEXT    | Observaciones del pedido                     |

---

## Relaciones

- `productos.categoria_id` referencia a `categorias.id`
- No hay relación directa entre comandas y productos, ya que los productos pedidos se almacenan como texto en la tabla `comandas`.

---

## Notas

- El sistema inicializa la base de datos y crea tablas si no existen.
- Se insertan datos por defecto al iniciar por primera vez.
