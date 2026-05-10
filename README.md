# S. Valvo y Cía — Panel de Administración

Sistema de gestión interna para una mueblería a medida. Permite presupuestar pedidos, hacer seguimiento del estado de producción mediante un tablero kanban, registrar pagos y configurar precios de líneas de muebles.

Proyecto de tesis universitaria. Aplicación web Flask que corre en red LAN local.

---

## Tecnologías

| Capa | Herramienta |
|---|---|
| Backend | Python 3 + Flask 3.1 |
| Base de datos | SQLite (via SQLAlchemy 2.0) |
| Migraciones | Flask-Migrate / Alembic |
| Autenticación | Flask-Login |
| Generación PDF | ReportLab + Pillow |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Gráficos | Chart.js (CDN) |
| Drag & drop | SortableJS (CDN) |

---

## Estructura del proyecto

```
Trabajo_Final/
├── run.py                      # Punto de entrada: crea la app y la levanta
├── requirements.txt            # Dependencias Python
│
├── instance/
│   ├── app.db                  # Base de datos SQLite (generada automáticamente)
│   └── uploads/comprobantes/   # Archivos de comprobantes de pago subidos
│
├── migrations/                 # Historial de migraciones de esquema (Alembic)
│
└── app/
    ├── __init__.py             # Fábrica de la aplicación (create_app)
    ├── models.py               # Modelos de base de datos (ORM)
    ├── auth.py                 # Rutas de autenticación (login / logout)
    ├── routes.py               # Todas las rutas del negocio
    │
    ├── templates/
    │   ├── base.html           # Layout base con sidebar (herencia Jinja2)
    │   ├── login.html          # Pantalla de ingreso (standalone, no extiende base)
    │   ├── dashboard.html      # KPIs, gráficos y tabla de últimos pedidos
    │   ├── pedidos.html        # Tablero kanban de pedidos
    │   ├── presupuestador.html # Formulario de creación de presupuesto/pedido
    │   ├── productos.html      # ABM de productos independientes
    │   ├── configuracion.html  # Precios de muebles a medida por línea
    │   └── partials/
    │       └── pedido_modal.html  # Modal de detalle y pago (incluido en dashboard y pedidos)
    │
    └── static/
        ├── styles.css          # Estilos globales: sidebar, kanban, modales, KPIs
        ├── img/
        │   └── logo.png        # Logo de la empresa
        ├── css/
        │   ├── login.css       # Estilos de la pantalla de ingreso
        │   ├── dashboard.css   # Estilos del dashboard (KPI cards, charts, tabla)
        │   ├── productos.css   # Estilos de la página de productos
        │   ├── configuracion.css  # Estilos de la página de configuración
        │   └── presupuestador.css # Estilos del presupuestador
        └── js/
            ├── base.js         # Scripts globales: alerts flash, sidebar activo
            ├── dashboard.js    # Chart.js, carrusel de gráficos, filtro de tabla
            ├── pedidos.js      # Kanban: SortableJS, colapsar cards, papelera
            ├── pedido_modal.js # Modal de detalle: edición inline, pagos, contacto
            ├── presupuestador.js # Constructor de muebles, resumen, items
            ├── productos.js    # Filtro de módulos, edición inline de stock
            └── configuracion.js  # Edición de precios, aumento porcentual, fecha
```

---

## Modelos de datos

### `User`
Usuario del sistema. Al iniciar la app se crea automáticamente `admin / admin123` si no existe ninguno.

### `Producto`
Producto independiente (electrodomésticos, griferías, etc.) con nombre, tipo, precio y stock opcional.

### `PrecioMueble`
Precio de un mueble a medida según línea (Standard, Roble, Lujo, Glaciar Laqueado) y medida en centímetros. Tiene tres variantes de precio: mueble sin mesada, alacena y mesada de acero inox.

### `AdicionalMueble`
Ítem adicional con cargo para cada línea (bisagras soft-close, cajoneras, etc.).

### `Pedido`
Pedido de un cliente. Tiene estado (`PENDIENTE` → `EN_CURSO` → `FINALIZADO`), timestamps por estado, monto total, seña y relación con ítems y pagos.

### `PedidoItem`
Línea de detalle de un pedido: descripción libre, cantidad, subtotal. Puede referenciar un `Producto` (para descontar stock) o ser un ítem de mueble a medida.

### `Pago`
Registro de un pago parcial de un pedido. Soporta efectivo, transferencia, MercadoPago y tarjeta (con cuotas y monto por cuota). Puede tener comprobantes adjuntos.

### `PagoComprobante`
Archivo subido como comprobante de pago (PDF o imagen).

### `ConfiguracionGeneral`
Almacena la fecha de última actualización de precios de muebles.

---

## Módulos del backend

### `app/__init__.py` — Fábrica de la app

```python
def create_app():
    # 1. Crea la instancia Flask con configuración SQLite en /instance/app.db
    # 2. Inicializa SQLAlchemy, Flask-Migrate y Flask-Login
    # 3. Crea las tablas y el usuario admin si no existen (db.create_all + seed)
    # 4. Registra los blueprints de auth y routes
```

### `app/auth.py` — Autenticación

- `GET /login` — Muestra el formulario de login
- `POST /login` — Valida usuario/contraseña y abre sesión con Flask-Login
- `GET /logout` — Cierra sesión y redirige al login

### `app/routes.py` — Rutas del negocio

#### Dashboard
- `GET /` y `GET /dashboard` — KPIs (totales por estado), últimos pedidos, datos para gráficos Chart.js

#### Presupuestador
- `GET /presupuestador` — Formulario con productos y precios de muebles (pasados al JS via `window.PRECIOS_MUEBLES`)
- `POST /presupuestador/crear_pedido` — Crea el `Pedido` + sus `PedidoItem` en la BD

#### Pedidos (Kanban)
- `GET /pedidos` — Tres listas de pedidos por estado para el tablero
- `POST /pedidos/mover/<id>` — Cambia el estado de un pedido (drag & drop)
- `POST /pedidos/eliminar/<id>` — Elimina lógicamente un pedido

#### API de pedidos (AJAX)
- `GET /api/pedidos/<id>` — Devuelve JSON completo del pedido (items, pagos, debe)
- `PATCH /api/pedidos/<id>` — Actualiza dirección/teléfono/email/observaciones
- `POST /api/pedidos/<id>/pagos` — Registra un nuevo pago (con comprobante opcional)
- `DELETE /api/pagos/<id>` — Elimina un pago
- `GET /pedidos/<id>/pdf` — Genera y devuelve el PDF del presupuesto

#### Productos
- `GET /productos` — Lista de productos agrupados por tipo
- `POST /productos` — Agrega un nuevo producto
- `POST /productos/<id>/delete` — Elimina un producto
- `POST /productos/<id>/stock` — Actualiza el stock via AJAX

#### Configuración
- `GET /configuracion` — Formulario con precios de muebles por línea
- `POST /configuracion` — Guarda cambios de precios (batch update)
- `POST /configuracion/agregar` — Agrega mueble o adicional a una línea
- `POST /configuracion/eliminar/<id>` — Elimina mueble o adicional
- `POST /configuracion/fecha` — Actualiza la fecha de precios

---

## Módulos del frontend (JS)

### `base.js`
Se ejecuta en todas las páginas. Cierra automáticamente los alertas flash después de 3 segundos y marca el link activo del sidebar según la URL actual. También expande el submenú de Productos si la ruta actual es `/productos` o `/configuracion`.

### `dashboard.js`
Inicializa tres gráficos Chart.js usando `window.DASHBOARD_DATA` inyectado desde Jinja2:
- **Dona**: distribución de montos por estado. Click en un segmento navega a `/pedidos?estado=...`
- **Línea**: ventas (suma de totales) por día en los últimos 7 días
- **Barras**: productos más vendidos por cantidad

También maneja el carrusel de gráficos (flechas izquierda/derecha) y el filtro en tiempo real de la tabla expandida de pedidos (debounce de 200ms).

### `pedidos.js`
Tablero kanban con SortableJS. Permite arrastrar cards entre las columnas PENDIENTE, EN_CURSO y FINALIZADO. Al soltar en otra columna hace `POST /pedidos/mover/<id>` para persistir el nuevo estado. Incluye zona de papelera para eliminar arrastrando, y toggle de colapso/expansión de cada card.

### `pedido_modal.js`
El script más complejo. Maneja dos modales anidados de Bootstrap:

1. **Modal de detalle del pedido** (`#modalPedido`):
   - Carga datos via `GET /api/pedidos/<id>`
   - Permite edición inline de dirección, teléfono, email y observaciones (toggle span ↔ input, guarda con `PATCH`)
   - Genera links de WhatsApp (app o web según dispositivo), Google Maps y Gmail con datos prellenados
   - Muestra historial de pagos con botones Ver y Eliminar
   - Botón Imprimir abre el PDF en nueva pestaña

2. **Modal de registrar pago** (`#modalPago`):
   - Soporta Efectivo, Transferencia, MercadoPago y Tarjeta (con cuotas)
   - Permite adjuntar un comprobante (PDF/imagen) con preview y barra de progreso XHR
   - Valida que el monto no supere el saldo pendiente antes de enviar

### `presupuestador.js`
Lógica del constructor de muebles a medida:
- Usa `window.PRECIOS_MUEBLES` para calcular el precio más cercano a la medida ingresada (busca la medida ≤ solicitada dentro de la línea seleccionada)
- Los tres tipos de componente (sin mesada / alacena / inox) son radios exclusivos; al seleccionar uno recalcula el precio
- "Agregar recomendación" agrega el mueble al resumen **sin** limpiar el constructor (permite apilar módulos)
- "Cancelar" limpia el constructor Y vacía el resumen completo
- Gestiona también la lista de ítems de productos independientes con botones ✕ por ítem

### `productos.js`
Página de productos independientes:
- Checkbox "Tiene stock" habilita/deshabilita el campo de cantidad al crear
- Campo de búsqueda filtra módulos y cards en tiempo real; expande automáticamente los grupos que tienen coincidencias
- Edición inline del stock: abre un mini-formulario dentro de la card, guarda via `POST /productos/<id>/stock` y actualiza el badge sin recargar la página

### `configuracion.js`
Página de configuración de precios:
- Cards colapsables por línea (Standard, Roble, Lujo, Glaciar Laqueado)
- Cada card tiene su propia toolbar con: selección múltiple, aplicar aumento porcentual (recalcula el valor en el input sin guardar aún), guardar/cancelar
- Barra de controles globales (arriba): selecciona todos los checks de todas las cards y aplica el porcentaje de golpe
- AJAX para agregar/eliminar filas de muebles y adicionales sin recargar
- Gestión de la fecha de actualización de precios con edición inline

---

## Cómo levantar el proyecto

```bash
# 1. Clonar y entrar al directorio
git clone <repo>
cd Trabajo_Final

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# 3. Levantar la app
python run.py
# Acceder en: http://localhost:5000
# Usuario: admin | Contraseña: admin123
```

> La base de datos `instance/app.db` se crea automáticamente al primer inicio.
> Para acceder desde otras PCs de la red: `http://<IP-del-servidor>:5000`

---

## Migraciones de base de datos

```bash
# Crear una migración nueva (después de modificar models.py)
flask db migrate -m "descripcion del cambio"

# Aplicar migraciones pendientes
flask db upgrade

# Ver historial
flask db history
```

---

## Convenciones del código

- **CSS por página**: cada template tiene su propio archivo en `static/css/`. Los estilos globales (sidebar, kanban, modales) están en `static/styles.css`.
- **JS por página**: cada template carga su propio archivo en `static/js/`. El código compartido por todas las páginas está en `static/js/base.js`.
- **Datos Jinja2 → JS**: se usa el patrón `window.VAR = {{ data | tojson }};` en un bloque `<script>` inline mínimo en el template. La lógica real vive en el archivo `.js` externo.
- **Sin comentarios obvios**: los nombres de funciones y variables son descriptivos. Los comentarios explican el *por qué* o la *lógica no obvia*, no el *qué*.
