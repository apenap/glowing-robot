# Referencia de API

El sistema ofrece algunos endpoints API para interacción en tiempo real, principalmente para la vista de cocina.

---

## 1. Obtener comandas pendientes

**GET** `/cocina/api/comandas`

**Respuesta:**
```json
[
  {
    "id": 1,
    "mesa": "3",
    "producto": "Hamburguesa",
    "precio": 70.0,
    "cantidad": 2,
    "fecha": "2025-07-02 18:32:11",
    "estado": "pendiente",
    "tipo_servicio": "Aquí",
    "observaciones": "Sin cebolla"
  },
  ...
]
```

---

## 2. Marcar comanda como completada

**POST** `/cocina/api/completar/<id_comanda>`

**Respuesta (éxito):**
```json
{ "success": true }
```

**Respuesta (fallo):**
```json
{ "success": false }
```

---

## Notas

- Ambos endpoints requieren sesión iniciada con rol de cocina o admin.
- Los endpoints son utilizados por AJAX en la interfaz de cocina.
