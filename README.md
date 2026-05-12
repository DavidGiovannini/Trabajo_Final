# S. Valvo y Cía — Sistema de Gestión de Pedidos

Aplicación web interna para la gestión de pedidos, presupuestos, productos y cobros de **S. Valvo y Cía**, fábrica de muebles a medida de Rafaela, Santa Fe.

Desarrollada como proyecto de tesis universitaria.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Framework web | Flask 3.1.2 |
| ORM / BD | SQLAlchemy 2.0 + SQLite (Flask-SQLAlchemy 3.1) |
| Migraciones | Flask-Migrate 4.1 (Alembic) |
| Autenticación | Flask-Login 0.6 |
| Generación PDF | ReportLab 4.4 + Pillow 12.1 |
| Frontend | Bootstrap 5 + Bootstrap Icons + Chart.js |
| Servidor WSGI | Werkzeug (desarrollo) |

---

## Estructura del proyecto

```
Trabajo_Final/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── auth.py              # Rutas de login/logout + rate limiting
│   ├── models.py            # Modelos ORM (User, Pedido, Producto, ...)
│   ├── routes.py            # Todas las rutas HTTP de la aplicación
│   ├── static/
│   │   ├── css/             # Hojas de estilo por módulo
│   │   ├── js/              # Scripts por módulo
│   │   └── img/             # Logo y recursos gráficos
│   └── templates/
│       ├── base.html        # Layout base (navbar, flashes, footer)
│       ├── login.html
│       ├── dashboard.html
│       ├── pedidos.html
│       ├── productos.html
│       ├── configuracion.html
│       ├── presupuestador.html
│       ├── calendario.html
│       └── partials/        # Fragmentos reutilizables (modal de pedido, etc.)
├── instance/
│   ├── app.db               # Base de datos SQLite (generada automáticamente)
│   ├── secret.key           # Clave secreta Flask (generada en el primer inicio)
│   └── uploads/
│       └── comprobantes/    # Archivos adjuntos de pagos
├── migrations/              # Carpeta de migraciones Alembic
├── requirements.txt
└── run.py                   # Punto de entrada: flask run / python run.py
```

---

## Instalación y configuración

### Requisitos previos

- Python 3.10 o superior
- pip

### Pasos

```bash
# 1. Clonar o descomprimir el proyecto
cd Trabajo_Final

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar la aplicación
python run.py
# o bien:
flask --app app run --debug
```

Al primer inicio, Flask crea automáticamente:
- `instance/app.db` con todas las tablas
- `instance/secret.key` con una clave aleatoria persistente
- El usuario administrador por defecto

### Credenciales por defecto

| Campo | Valor |
|---|---|
| Usuario | `admin` |
| Contraseña | `admin123` |

> **Cambiar la contraseña después del primer inicio** es altamente recomendado.

---

## Funcionalidades

### Dashboard
- KPIs en tiempo real: total de pedidos, pendientes, en curso y finalizados.
- Gráfico de torta: distribución por estado (monto $ o cantidad #).
- Gráfico de línea: pedidos por día (últimos 7, 30 o 90 días).
- Gráfico de barras: top-5 productos más vendidos.
- Gráfico de evolución mensual: últimos 6 meses.
- Tabla de últimos 5 pedidos con acceso directo al modal de detalle.
- Todos los gráficos pueden expandirse a pantalla completa con filtros.

### Pedidos (Kanban)
- Vista en tres columnas: **Pendiente**, **En Curso**, **Finalizado**.
- Arrastrar y soltar (drag & drop) para cambiar el estado de un pedido.
- Modal de detalle con información completa: datos del cliente, ítems, historial de pagos.
- Edición inline de datos del cliente (dirección, teléfono, email, observaciones).
- Eliminación de seña registrada.
- Descuento automático de stock al finalizar un pedido (una sola vez).
- Borrado lógico: los pedidos finalizados se marcan como `activo=False` en lugar de eliminarse.

### Presupuestador
- Herramienta interactiva para armar presupuestos con:
  - Muebles a medida por línea (standard, melamina, glaciar, lujo, roble) y medida.
  - Adicionales por línea (zócalos, herrajes, etc.).
  - Productos del catálogo (electrodomésticos, accesorios).
- Cálculo automático de subtotales y total.
- Opción de registrar seña con forma de pago.
- Al confirmar, crea un Pedido con sus ítems y redirige al kanban.

### Productos
- Catálogo agrupado por tipo de producto en acordeones colapsables.
- Filtro de búsqueda en tiempo real por nombre o tipo.
- Edición inline del precio (ícono lápiz → guardar vía AJAX).
- Actualización masiva de precios por porcentaje de aumento.
- Gestión de stock individual por producto.
- Alta y baja de productos.

### Configuración de precios
- Tabla de precios de muebles por línea y medida (base / alacena / inox).
- Gestión de adicionales por línea.
- Fecha de última actualización de precios.
- Alta, edición y baja de filas en formularios dinámicos.

### Pagos
- Registro de pagos parciales o totales por pedido.
- Métodos soportados: Efectivo, Transferencia, Tarjeta (con cuotas y monto/cuota).
- Subida de comprobantes adjuntos (PDF, PNG, JPEG).
- Historial de pagos en el modal de detalle del pedido.
- Cálculo automático del saldo pendiente (total − seña − pagos registrados).

### PDFs
- **Presupuesto**: PDF profesional con logo, datos del cliente, detalle de ítems, total y condiciones de pago. Accesible con login (`/pedidos/<id>/pdf`) o vía enlace público con token único (`/p/<token>`).
- **Remito interno**: PDF con tabla de ítems, casilleros de firma y observaciones. Solo accesible con login.

### Calendario / Recordatorios
- Calendario mensual interactivo con vista de eventos.
- CRUD completo de recordatorios con título, descripción, fecha, hora y color.
- Widget de "próximos recordatorios (7 días)" en el dashboard.

---

## Seguridad

- Contraseñas hasheadas con `pbkdf2:sha256` (Werkzeug).
- **Rate limiting** en login: 5 intentos fallidos bloquean la IP por 5 minutos (en memoria).
- Protección anti-open-redirect en el parámetro `next` del login.
- Cookies de sesión con `HttpOnly=True` y `SameSite=Lax`.
- Clave secreta generada aleatoriamente y persistida en `instance/secret.key`.
- Todas las rutas (excepto login y `/p/<token>`) requieren autenticación (`@login_required`).
- Subida de archivos restringida a `application/pdf`, `image/png` e `image/jpeg`.
- Nombres de archivo saneados con `werkzeug.utils.secure_filename` + prefijo único.

---

## Modelos de base de datos

```
User                  id, username, password_hash
Producto              id, nombre, tipo, precio, stock
PrecioMueble          id, linea, medida, base, alacena, inox
AdicionalMueble       id, linea, nombre, precio_base, precio_alacena, precio_inox
ConfiguracionPrecio   id, clave, valor
ConfiguracionGeneral  id, fecha_actualizacion
Pedido                id, cliente, telefono, email, direccion, ..., estado,
                          total, monto_sena, forma_pago_preferida,
                          activo, stock_descontado, token_pdf,
                          created_at, pendiente_at, en_curso_at, finalizado_at
PedidoItem            id, pedido_id, producto_id (nullable), descripcion,
                          cantidad, metros, subtotal
Pago                  id, pedido_id, metodo, monto_pagado, cuotas,
                          monto_cuota, fecha_pago, created_at
PagoComprobante       id, pago_id, filename, original_name, mimetype,
                          size_bytes, uploaded_at
Recordatorio          id, titulo, descripcion, fecha, hora, color,
                          completado, notificado, created_at
```

---

## Rutas principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Redirige a `/dashboard` |
| GET | `/dashboard` | Dashboard con KPIs y gráficos |
| GET/POST | `/productos` | Catálogo de productos |
| POST | `/productos/<id>/precio` | Actualizar precio individual (AJAX) |
| POST | `/productos/bulk_precio` | Actualizar precios en masa (AJAX) |
| POST | `/productos/<id>/stock` | Actualizar stock (AJAX) |
| GET/POST | `/configuracion` | Precios de muebles y adicionales |
| GET | `/presupuestador` | Herramienta de presupuestos |
| POST | `/presupuestador/crear_pedido` | Crear pedido desde presupuesto |
| GET | `/pedidos` | Kanban de pedidos |
| POST | `/pedidos/mover/<id>` | Cambiar estado de pedido (AJAX) |
| POST | `/pedidos/eliminar/<id>` | Eliminar/desactivar pedido (AJAX) |
| GET | `/api/pedidos/<id>` | Detalle JSON de un pedido |
| PATCH | `/api/pedidos/<id>` | Editar datos del pedido (AJAX) |
| GET | `/pedidos/<id>/pdf` | Descargar presupuesto PDF (login) |
| GET | `/p/<token>` | Descargar presupuesto PDF (público) |
| GET | `/pedidos/<id>/remito` | Descargar remito PDF |
| POST | `/api/pedidos/<id>/pagos` | Registrar pago |
| DELETE | `/api/pagos/<id>` | Eliminar pago |
| GET | `/calendario` | Vista del calendario |
| GET/POST | `/api/recordatorios` | Listar / crear recordatorios |
| PATCH/DELETE | `/api/recordatorios/<id>` | Editar / eliminar recordatorio |
| GET | `/login` | Pantalla de inicio de sesión |
| GET | `/logout` | Cerrar sesión |
