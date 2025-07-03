# sistema_restaurante.py
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify, flash
import sqlite3
import datetime
import os
from werkzeug.utils import secure_filename
import html as html_lib

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura' # ¡Cambia esto en un entorno de producción!

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

hora_inicio = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
archivo_log = f'log_{hora_inicio}.txt'

def log(texto):
    tiempo = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(archivo_log, "a", encoding="utf-8") as f:
        f.write(f"{tiempo} {texto}\n")
    print(texto)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with sqlite3.connect("restaurante.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio REAL NOT NULL,
                imagen TEXT DEFAULT 'default.jpg',
                categoria_id INTEGER,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mesa TEXT,
                producto TEXT,
                precio REAL,
                cantidad INTEGER DEFAULT 1,
                fecha TEXT,
                estado TEXT DEFAULT 'pendiente',
                tipo_servicio TEXT DEFAULT 'Aquí',
                observaciones TEXT
            )
        """)
        try:
            conn.execute("ALTER TABLE comandas ADD COLUMN tipo_servicio TEXT DEFAULT 'Aquí'")
        except sqlite3.OperationalError: pass
        try:
            conn.execute("ALTER TABLE comandas ADD COLUMN observaciones TEXT")
        except sqlite3.OperationalError: pass

        try:
            conn.executemany("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)",
                             [('Bebidas',), ('Comidas',), ('Postres',)])
            conn.executemany("INSERT OR IGNORE INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                             [('admin', 'adminpass', 'admin'),
                              ('cocina', 'cocinapass', 'cocina'),
                              ('mesero', 'meseropass', 'mesero')])
            conn.commit()
            log("Datos iniciales verificados/insertados.")
        except sqlite3.Error as e:
            log(f"Error al insertar datos iniciales: {e}")

def acceso_restringido(rol_requerido):
    if 'rol' not in session or session['rol'] not in rol_requerido:
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('login'))
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("restaurante.db") as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (username, password)).fetchone()
            if user:
                session['username'] = user['username']
                session['rol'] = user['rol']
                if user['rol'] == 'admin': return redirect(url_for('vista_admin'))
                if user['rol'] == 'cocina': return redirect(url_for('vista_cocina'))
                if user['rol'] == 'mesero': return redirect(url_for('vista_pos'))
            else:
                flash("Usuario o contraseña incorrectos", "danger")
                return redirect(url_for('login'))
    
    LOGIN_TEMPLATE = """
    <!DOCTYPE html><html lang="es"><head><title>Login</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"/>
    <style>body { display: flex; justify-content: center; align-items: center; min-height: 100vh; }</style>
    </head><body><main class="container" style="max-width: 450px;">
    <article><h2 align="center">Iniciar Sesión</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for category, message in messages %}
            <p><mark>{{ message }}</mark></p>
        {% endfor %}{% endif %}{% endwith %}
        <form method="post">
            <input type="text" name="username" placeholder="Usuario" required autocomplete="username">
            <input type="password" name="password" placeholder="Contraseña" required autocomplete="current-password">
            <button type="submit">Entrar</button>
        </form>
    </article></main></body></html>"""
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for('login'))

# --- VISTA MESERO (POS) ---
@app.route('/pos', methods=['GET', 'POST'])
def vista_pos():
    restringido = acceso_restringido(['mesero'])
    if restringido: return restringido

    with sqlite3.connect("restaurante.db") as conn:
        conn.row_factory = sqlite3.Row
        if request.method == 'POST':
            data = request.get_json()
            mesa = data.get('mesa')
            tipo_servicio = data.get('tipo_servicio')
            observaciones = data.get('observaciones')
            pedido = data.get('pedido')
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for item in pedido:
                conn.execute(
                    """INSERT INTO comandas 
                       (mesa, producto, precio, cantidad, fecha, tipo_servicio, observaciones) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (mesa, item['nombre'], item['precio'], item['cantidad'], 
                     fecha_actual, tipo_servicio, observaciones)
                )
            conn.commit()
            log(f"📝 Comanda guardada para Mesa {mesa} con {len(pedido)} items.")
            return jsonify({"success": True, "message": "Comanda guardada correctamente"})

        categorias = conn.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
        productos_por_categoria = {}
        for cat in categorias:
            productos_rows = conn.execute("SELECT * FROM productos WHERE categoria_id=? ORDER BY nombre", (cat['id'],)).fetchall()
            productos_por_categoria[cat['nombre']] = [dict(row) for row in productos_rows]

    POS_HTML = """
    <!DOCTYPE html><html lang="es"><head><title>Punto de Venta</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"/>
    <style>
      body { overflow: hidden; }
      main { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; height: 100vh; padding: 0; }
      .menu-section, .order-section { overflow-y: auto; height: 100vh; padding: 1.5rem; }
      .order-section { background-color: var(--card-background-color); border-left: var(--card-border); }
      .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
      .product-card { cursor: pointer; text-align: center; }
      .product-card img { width: 100%; height: 100px; object-fit: cover; border-radius: var(--border-radius); }
      .product-card:hover { transform: scale(1.03); transition: transform 0.2s ease-out; }
      .order-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
      #order-total { text-align: right; font-size: 1.5em; margin: 1rem 0; }
    </style></head>
    <body>
    <main>
      <section class="menu-section">
        <header style="display:flex; justify-content:space-between; align-items:center;">
            <h2>Menú</h2> <a href="/logout" role="button" class="secondary outline">Cerrar Sesión</a>
        </header>
        {% for cat_name, productos in productos_por_categoria.items() %}
        <details open>
          <summary role="button" class="outline">{{ cat_name }}</summary>
          <div class="product-grid">
            {% for p in productos %}
            <article class="product-card" onclick='addToOrder({{ p | tojson | safe }})'>
                <img src="{{ url_for('static', filename='img/' + p.imagen) }}" alt="{{ p.nombre }}">
                <footer><small>{{ p.nombre }}</small><br><strong>${{ "%.2f"|format(p.precio) }}</strong></footer>
            </article>
            {% endfor %}
          </div>
        </details>
        {% endfor %}
      </section>
      <aside class="order-section">
        <h2>Pedido</h2>
        <div class="grid">
            <label for="mesa">Mesa <select id="mesa">{% for i in range(1, 11) %}<option value="{{i}}">Mesa {{i}}</option>{% endfor %}</select></label>
            <label for="tipo_servicio">Servicio <select id="tipo_servicio"><option value="Aquí">Para Aquí</option><option value="Llevar">Para Llevar</option></select></label>
        </div>
        <div id="order-summary" style="flex-grow:1;"></div>
        <div id="order-total">Total: $0.00</div>
        <label for="observaciones">Observaciones</label>
        <textarea id="observaciones" rows="3"></textarea>
        <button class="contrast" onclick="saveOrder()">✓ Guardar Comanda</button>
      </aside>
    </main>
    <script>
        let currentOrder = [];
        function addToOrder(product) { const existingItem = currentOrder.find(item => item.id === product.id); if (existingItem) { existingItem.cantidad++; } else { currentOrder.push({ ...product, cantidad: 1 }); } renderOrder(); }
        function removeFromOrder(productId) { const itemIndex = currentOrder.findIndex(item => item.id === productId); if (itemIndex > -1) { currentOrder[itemIndex].cantidad--; if (currentOrder[itemIndex].cantidad === 0) { currentOrder.splice(itemIndex, 1); } } renderOrder(); }
        function renderOrder() { const summaryDiv = document.getElementById('order-summary'); summaryDiv.innerHTML = ''; let total = 0; currentOrder.forEach(item => { const itemDiv = document.createElement('div'); itemDiv.className = 'order-item'; itemDiv.innerHTML = `<div>${item.nombre}<br><small>x${item.cantidad}</small></div><div><strong>$${(item.precio * item.cantidad).toFixed(2)}</strong> <a href="#" onclick="event.preventDefault(); removeFromOrder(${item.id})">❌</a></div>`; summaryDiv.appendChild(itemDiv); total += item.precio * item.cantidad; }); document.getElementById('order-total').innerText = `Total: $${total.toFixed(2)}`; }
        function saveOrder() { if (currentOrder.length === 0) { alert("El pedido está vacío."); return; } const orderData = { mesa: document.getElementById('mesa').value, tipo_servicio: document.getElementById('tipo_servicio').value, observaciones: document.getElementById('observaciones').value, pedido: currentOrder }; fetch('/pos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(orderData) }).then(response => response.json()).then(data => { if(data.success) { alert(data.message); currentOrder = []; renderOrder(); document.getElementById('observaciones').value = ''; } else { alert("Error al guardar la comanda."); } }); }
    </script>
    </body></html>"""
    return render_template_string(POS_HTML, productos_por_categoria=productos_por_categoria)


# --- VISTAS DE COCINA Y APIs ---
@app.route('/cocina')
def vista_cocina():
    restringido = acceso_restringido(['cocina'])
    if restringido: return restringido
    
    COCINA_HTML = """
    <!DOCTYPE html><html lang="es" data-theme="dark"><head><title>Vista de Cocina</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"/>
    <style> .comandas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; } </style>
    </head><body>
    <main class="container">
      <header style="display:flex; justify-content:space-between; align-items:center;">
        <h2>Comandas Pendientes</h2><a href="/logout" role="button" class="secondary outline">Cerrar Sesión</a>
      </header>
      <div id="comandas-container" class="comandas-grid"></div>
    </main>
    <script>
      function renderComandas(comandas) {
          const container = document.getElementById('comandas-container');
          container.innerHTML = '';
          if (comandas.length === 0) {
              container.innerHTML = '<article><p align="center">No hay comandas pendientes.</p></article>'; return;
          }
          comandas.forEach(comanda => {
              const card = document.createElement('article');
              const tipoIcon = comanda.tipo_servicio === 'Aquí' ? '🍴' : '🛍️';
              const obsHTML = comanda.observaciones ? `<blockquote>Nota: ${comanda.observaciones}</blockquote>` : '';
              card.innerHTML = `
                  <header>
                      <div style="display:flex; justify-content:space-between;">
                          <strong>Mesa: ${comanda.mesa}</strong> <span>${tipoIcon} ${comanda.tipo_servicio}</span>
                      </div>
                  </header>
                  <h4>${comanda.producto} (x${comanda.cantidad})</h4>
                  <small>Pedido a las ${new Date(comanda.fecha).toLocaleTimeString()}</small>
                  ${obsHTML}
                  <footer><button onclick="completeOrder(${comanda.id})">Marcar como Listo</button></footer>`;
              container.appendChild(card);
          });
      }
      function fetchComandas() { fetch('/cocina/api/comandas').then(response => response.json()).then(data => renderComandas(data)); }
      function completeOrder(id) { fetch(`/cocina/api/completar/${id}`, { method: 'POST' }).then(response => response.json()).then(data => { if (data.success) fetchComandas(); }); }
      setInterval(fetchComandas, 10000); fetchComandas(); // Refresca cada 10 segundos
    </script>
    </body></html>"""
    return COCINA_HTML

@app.route('/cocina/api/comandas')
def api_cocina_comandas():
    restringido = acceso_restringido(['cocina', 'admin'])
    if restringido: return jsonify([])
    with sqlite3.connect("restaurante.db") as conn:
        conn.row_factory = sqlite3.Row
        comandas = conn.execute("SELECT * FROM comandas WHERE estado='pendiente' ORDER BY id ASC").fetchall()
        return jsonify([dict(c) for c in comandas])

@app.route('/cocina/api/completar/<int:comanda_id>', methods=['POST'])
def api_cocina_completar(comanda_id):
    restringido = acceso_restringido(['cocina', 'admin'])
    if restringido: return jsonify({"success": False})
    with sqlite3.connect("restaurante.db") as conn:
        conn.execute("UPDATE comandas SET estado='completado' WHERE id=?", (comanda_id,))
        conn.commit()
    log(f"✅ Comanda completada por API: ID {comanda_id}")
    return jsonify({"success": True})


# --- VISTA Y RUTAS DE ADMINISTRADOR ---
@app.route('/admin')
def vista_admin():
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido

    with sqlite3.connect("restaurante.db") as conn:
        conn.row_factory = sqlite3.Row
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        total_hoy = conn.execute("SELECT SUM(precio * cantidad) FROM comandas WHERE date(fecha)=?", (hoy_str,)).fetchone()[0] or 0
        total_historico = conn.execute("SELECT SUM(precio * cantidad) FROM comandas").fetchone()[0] or 0
        total_comandas = conn.execute("SELECT COUNT(DISTINCT id) FROM comandas").fetchone()[0] or 0 # Corregido para contar comandas únicas
        mas_vendido = conn.execute("SELECT producto, SUM(cantidad) as total FROM comandas GROUP BY producto ORDER BY total DESC LIMIT 1").fetchone()
        
        all_comandas = conn.execute("SELECT * FROM comandas ORDER BY fecha DESC").fetchall()
        usuarios = conn.execute("SELECT id, username, rol FROM usuarios").fetchall()
        categorias = conn.execute("SELECT * FROM categorias ORDER BY nombre").fetchall()
        productos = conn.execute("""
            SELECT p.id, p.nombre, p.precio, p.imagen, c.nombre as categoria_nombre, c.id as categoria_id
            FROM productos p JOIN categorias c ON p.categoria_id = c.id ORDER BY p.nombre
        """).fetchall()

    kpis = {
        "total_hoy": f"${total_hoy:,.2f}", "total_historico": f"${total_historico:,.2f}", "total_comandas": total_comandas,
        "mas_vendido": f"{mas_vendido['producto']} ({mas_vendido['total']})" if mas_vendido else "N/A",
    }
    
    ADMIN_HTML = """
    <!DOCTYPE html><html lang="es"><head><title>Admin Panel</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"/>
    <style>
      .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
      .kpi-card h4 { color: var(--muted-color); } .kpi-card p { font-size: 2em; font-weight: bold; margin: 0; }
      .form-inline { display: flex; gap: 0.5rem; align-items: center; }
      td form { margin-bottom: 0; }
    </style></head>
    <body><main class="container">
      <header style="display:flex; justify-content:space-between; align-items:center;">
          <h2>Panel de Administración</h2> <a href="/logout" role="button" class="secondary outline">Cerrar Sesión</a>
      </header>
      {% with messages = get_flashed_messages(with_categories=true) %} {% if messages %}
        <article style="background-color: var(--card-background-color); border-color: var(--card-border-color);">
            {% for category, message in messages %} <p><mark>{{ message }}</mark></p> {% endfor %}
        </article>
      {% endif %} {% endwith %}
      
      <details open>
        <summary role="button">Dashboard</summary>
        <div class="kpi-grid">
          <article class="kpi-card"><h4>Ventas de Hoy</h4><p>{{ kpis.total_hoy }}</p></article>
          <article class="kpi-card"><h4>Ventas Históricas</h4><p>{{ kpis.total_historico }}</p></article>
          <article class="kpi-card"><h4>Total Comandas</h4><p>{{ kpis.total_comandas }}</p></article>
          <article class="kpi-card"><h4>Producto Más Vendido</h4><p style="font-size:1.5em;">{{ kpis.mas_vendido }}</p></article>
        </div>
      </details>
      
      <details><summary role="button" class="contrast outline">Gestión de Productos</summary>
        <article>
          <form action="{{ url_for('add_producto') }}" method="post" enctype="multipart/form-data">
            <div class="grid">
              <input type="text" name="nombre" placeholder="Nombre del producto" required>
              <input type="number" name="precio" placeholder="Precio" step="0.01" required>
            </div>
            <div class="grid">
              <select name="categoria_id" required><option value="">Seleccionar categoría...</option>{% for c in categorias %}<option value="{{c.id}}">{{c.nombre}}</option>{% endfor %}</select>
              <input type="file" name="imagen" accept="image/*">
            </div>
            <button type="submit">Añadir Producto</button>
          </form>
          <div style="overflow-x:auto;"><table>
            <thead><tr><th>Imagen</th><th>Nombre</th><th>Precio</th><th>Categoría</th><th>Acciones</th></tr></thead>
            <tbody>{% for p in productos %}<tr>
              <td><img src="{{ url_for('static', filename='img/' + p.imagen) }}" alt="{{p.nombre}}" width="50" height="50" style="object-fit:cover; border-radius: 50%;"></td>
              <td>{{p.nombre}}</td><td>${{"%.2f"|format(p.precio)}}</td><td>{{p.categoria_nombre}}</td>
              <td><form action="{{ url_for('delete_producto', id=p.id) }}" method="post" onsubmit="return confirm('¿Eliminar este producto?');"><button class="secondary outline">Eliminar</button></form></td>
            </tr>{% endfor %}</tbody>
          </table></div>
        </article>
      </details>
      
      <details><summary role="button" class="contrast outline">Gestión de Categorías</summary>
        <article>
          <form action="{{ url_for('add_categoria') }}" method="post" class="form-inline"><input type="text" name="nombre" placeholder="Nombre nueva categoría" required style="flex-grow:1;"><button type="submit">Añadir</button></form>
          <div style="overflow-x:auto;"><table>
            <thead><tr><th>Nombre Actual</th><th>Acciones</th></tr></thead>
            <tbody>{% for c in categorias %}<tr>
              <td><form action="{{ url_for('edit_categoria', id=c.id) }}" method="post" class="form-inline"><input type="text" name="nombre" value="{{c.nombre}}" required><button type="submit" class="outline">Guardar</button></form></td>
              <td><form action="{{ url_for('delete_categoria', id=c.id) }}" method="post" onsubmit="return confirm('¿Eliminar categoría?');"><button class="secondary outline">Eliminar</button></form></td>
            </tr>{% endfor %}</tbody>
          </table></div>
        </article>
      </details>
      
      <details><summary role="button">Historial de Comandas</summary>
        <div style="overflow-x:auto;"><table>
          <thead><tr><th>ID</th><th>Mesa</th><th>Producto</th><th>Cant.</th><th>Total</th><th>Fecha</th><th>Estado</th></tr></thead>
          <tbody>{% for c in all_comandas %}<tr><td>{{c.id}}</td><td>{{c.mesa}}</td><td>{{c.producto}}</td><td>{{c.cantidad}}</td><td>${{"%.2f"|format(c.precio*c.cantidad)}}</td><td>{{c.fecha}}</td><td>{{c.estado}}</td></tr>{% endfor %}</tbody>
        </table></div>
      </details>

    </main></body></html>"""
    return render_template_string(ADMIN_HTML, kpis=kpis, all_comandas=all_comandas, usuarios=usuarios, productos=productos, categorias=categorias)

# --- RUTAS CRUD PARA CATEGORÍAS ---
@app.route('/admin/categoria/add', methods=['POST'])
def add_categoria():
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido
    nombre = request.form['nombre']
    if nombre:
        try:
            with sqlite3.connect("restaurante.db") as conn:
                conn.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
                conn.commit()
            flash('Categoría añadida con éxito.', 'success')
            log(f"➕ Categoría añadida: {nombre}")
        except sqlite3.IntegrityError:
            flash('Error: La categoría ya existe.', 'danger')
    return redirect(url_for('vista_admin'))

@app.route('/admin/categoria/edit/<int:id>', methods=['POST'])
def edit_categoria(id):
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido
    nombre = request.form['nombre']
    if nombre:
        try:
            with sqlite3.connect("restaurante.db") as conn:
                conn.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nombre, id))
                conn.commit()
            flash('Categoría actualizada con éxito.', 'success')
            log(f"✏️ Categoría editada ID {id}: {nombre}")
        except sqlite3.IntegrityError:
            flash('Error: El nuevo nombre de la categoría ya existe.', 'danger')
    return redirect(url_for('vista_admin'))

@app.route('/admin/categoria/delete/<int:id>', methods=['POST'])
def delete_categoria(id):
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido
    try:
        with sqlite3.connect("restaurante.db") as conn:
            conn.execute("DELETE FROM categorias WHERE id = ?", (id,))
            conn.commit()
        flash('Categoría eliminada con éxito.', 'success')
        log(f"➖ Categoría eliminada ID: {id}")
    except sqlite3.IntegrityError:
        flash('Error: No se puede eliminar una categoría que contiene productos.', 'danger')
    except Exception as e:
        flash(f"Error inesperado: {e}", 'danger')
    return redirect(url_for('vista_admin'))

# --- RUTAS CRUD PARA PRODUCTOS ---
@app.route('/admin/producto/add', methods=['POST'])
def add_producto():
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido
    
    nombre = request.form['nombre']
    precio = request.form['precio']
    categoria_id = request.form['categoria_id']
    imagen_filename = 'default.jpg'

    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and allowed_file(file.filename):
            imagen_filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))

    try:
        with sqlite3.connect("restaurante.db") as conn:
            conn.execute("INSERT INTO productos (nombre, precio, categoria_id, imagen) VALUES (?, ?, ?, ?)",
                         (nombre, precio, categoria_id, imagen_filename))
            conn.commit()
        flash('Producto añadido con éxito.', 'success')
        log(f"➕ Producto añadido: {nombre}")
    except sqlite3.IntegrityError:
        flash('Error: Ya existe un producto con ese nombre.', 'danger')
    return redirect(url_for('vista_admin'))

@app.route('/admin/producto/delete/<int:id>', methods=['POST'])
def delete_producto(id):
    restringido = acceso_restringido(['admin'])
    if restringido: return restringido

    with sqlite3.connect("restaurante.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT imagen, nombre FROM productos WHERE id = ?", (id,))
        result = cursor.fetchone()
        if result:
            imagen_filename, nombre_producto = result
            cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
            conn.commit()
            if imagen_filename != 'default.jpg':
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename))
                except OSError as e:
                    flash(f"Error al eliminar el archivo de imagen: {e}", "danger")
                    log(f"⚠️ Error al eliminar archivo de imagen {imagen_filename}: {e}")
            flash(f'Producto "{nombre_producto}" eliminado con éxito.', 'success')
            log(f"➖ Producto eliminado: {nombre_producto}")
        else:
            flash('Error: Producto no encontrado.', 'danger')
    return redirect(url_for('vista_admin'))

if __name__ == '__main__':
    init_db()
    log("🚀 Servidor iniciado en http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
