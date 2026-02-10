from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFrame, QLabel,
    QPushButton, QLineEdit, QMessageBox, QDialog, QFormLayout, QCheckBox,
    QDoubleSpinBox, QSpacerItem, QSizePolicy, QStackedWidget, QSpinBox
)
from .ui_theme import apply_card_shadow
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

LOW_STOCK_THRESHOLD = 5  # <= este valor se considera "bajo stock"

# =========================
#   Estilos (QSS)
# =========================
PRODUCTS_QSS = """
/* Cards comunes (no forzar blanco; respetar theme oscuro) */
#ModuleCard, #AddCard, #ProductCard {
    background: #1b202a;
    border: 1px solid rgba(230,232,236,0.10);
    border-radius: 16px;
    padding: 16px;
}
#ModuleCard:hover, #AddCard:hover, #ProductCard:hover {
    border-color: #6ea8fe;
    box-shadow: 0 8px 24px rgba(79,110,247,0.12);
    background: #1e2430;
}

#AddCard { border-style: dashed; text-align: center; }
.CardTitle   { font-size: 16px; font-weight: 800; color: #F2F4F8; text-align:center; background: transparent; }
.CardSubtitle{ color: #9CA3AF; text-align:center; background: transparent; }

/* Badge de stock */
#StockBadge {
    background: #111827;
    color: #ffffff;
    border-radius: 12px;
    padding: 2px 8px;
    font-weight: 800;
    font-size: 12px;
}
#StockBadge[stock="zero"] { background: #ef4444; color: #ffffff; }   /* rojo */
#StockBadge[stock="low"]  { background: #f59e0b; color: #111827; }   /* ámbar */
#StockBadge[stock="ok"]   { background: #10b981; color: #ffffff; }   /* verde */

/* Botones */
.ActionBtn {
    background: #EEF2FF;
    color: #374151;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 600;
}
.ActionBtn:hover { background: #E0E7FF; }
.DangerBtn {
    background: #fee2e2; color: #7f1d1d;
    border-radius: 10px; padding: 6px 10px; font-weight: 600;
}
.DangerBtn:hover { background: #fecaca; }

#PrimaryBtn {
    background: #4f6ef7; color: #fff; font-weight: 700;
    border-radius: 10px; padding: 8px 14px;
}
#PrimaryBtn:pressed { background: #3f5ad3; }
#GhostBtn {
    background: transparent; border: 1px solid #e5e7eb; color:#374151;
    border-radius: 10px; padding: 8px 14px; font-weight: 600;
}

/* Encabezados */
#ViewHeader { border-bottom: 1px solid #eef2f7; padding-bottom: 8px; }
#HeaderTitle { font-size: 18px; font-weight: 800; }

/* Diálogos */
#DialogRoot { background: #ffffff; }
#DialogTitle { font-size: 18px; font-weight: 800; }
#DialogHint { color: #6b7280; }
#DialogFooter { border-top: 1px solid #eef2f7; padding-top: 8px; }
"""


# =========================
#   Diálogo de MÓDULO
# =========================
class ModuleDialog(QDialog):
    def __init__(self, parent=None, existentes=None):
        super().__init__(parent)
        self.setObjectName("BlueDialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#1b202a"))
        self.setPalette(pal)
        self.setWindowTitle("Nuevo módulo")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.existentes = existentes or set()
        self.resultado = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Nuevo módulo"); title.setObjectName("DialogTitle")
        hint  = QLabel("Ingresá el tipo de módulo (por ejemplo, Bajo Mesada).")
        hint.setObjectName("DialogHint")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        self.in_nombre = QLineEdit()

        form.addRow("Tipo de módulo:", self.in_nombre)

        footer = QHBoxLayout(); footer.setObjectName("DialogFooter")
        footer.addStretch(1)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.setObjectName("GhostBtn")
        btn_ok = QPushButton("Crear"); btn_ok.setObjectName("PrimaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._accept)

        root.addWidget(title); root.addWidget(hint)
        root.addSpacing(8)
        root.addLayout(form)
        root.addSpacing(8)
        footer.addWidget(btn_cancel); footer.addWidget(btn_ok)
        root.addLayout(footer)

    def _accept(self):
        nombre = self.in_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Dato requerido", "Completá el tipo de módulo.")
            return
        if nombre in self.existentes:
            QMessageBox.warning(self, "Duplicado", "Ya existe un módulo con ese nombre.")
            return
        self.resultado = nombre
        self.accept()

    def get_nombre(self):
        return self.resultado


# =========================
#   Diálogo de PRODUCTO
# =========================
class ProductDialog(QDialog):
    """Diálogo moderno para crear/editar un producto. Puede bloquear el 'tipo'."""
    def __init__(self, parent=None, data=None, lock_tipo=False, fixed_tipo=""):
        super().__init__(parent)
        self.setObjectName("BlueDialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor("#1b202a"))
        self.setPalette(pal)
        self.setWindowTitle("Producto")
        self.setModal(True)
        self.data = data or {}
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Producto"); title.setObjectName("DialogTitle")
        hint  = QLabel("Completá los datos del producto."); hint.setObjectName("DialogHint")

        form = QFormLayout(); form.setLabelAlignment(Qt.AlignRight)

        self.in_tipo = QLineEdit(self.data.get("tipo", fixed_tipo or ""))
        self.in_nombre = QLineEdit(self.data.get("nombre", self.data.get("material", "")))  # compat
        self.in_por_metro = QCheckBox("Precio por metro")
        self.in_por_metro.setChecked(self.data.get("por_metro", False))

        self.in_precio = QDoubleSpinBox()
        self.in_precio.setPrefix("$ ")
        self.in_precio.setDecimals(2)
        self.in_precio.setMaximum(10_000_000)
        self.in_precio.setValue(float(self.data.get("precio", 0.0)))
        self.in_precio.setEnabled(not self.in_por_metro.isChecked())

        # Stock opcional
        self.in_maneja_stock = QCheckBox("Stock")
        self.in_maneja_stock.setChecked(self.data.get("maneja_stock", self.data.get("stock_habilitado", False)))

        self.in_cantidad = QSpinBox()
        self.in_cantidad.setRange(0, 1_000_000)
        self.in_cantidad.setValue(int(self.data.get("cantidad", 0)))
        self.in_cantidad.setEnabled(self.in_maneja_stock.isChecked())

        # Conexiones
        self.in_por_metro.toggled.connect(lambda checked: self.in_precio.setEnabled(not checked))
        self.in_maneja_stock.toggled.connect(self.in_cantidad.setEnabled)

        # Form UI
        form.addRow("Tipo de módulo:", self.in_tipo)
        form.addRow("Nombre:", self.in_nombre)
        form.addRow("", self.in_por_metro)
        form.addRow("Precio unitario:", self.in_precio)
        form.addRow("", self.in_maneja_stock)
        form.addRow("Cantidad:", self.in_cantidad)

        if lock_tipo:
            self.in_tipo.setReadOnly(True)
            self.in_tipo.setEnabled(False)

        footer = QHBoxLayout(); footer.setObjectName("DialogFooter")
        footer.addStretch(1)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.setObjectName("GhostBtn")
        btn_ok = QPushButton("Guardar"); btn_ok.setObjectName("PrimaryBtn")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self._accept)

        root.addWidget(title); root.addWidget(hint)
        root.addSpacing(8)
        root.addLayout(form)
        root.addSpacing(8)
        footer.addWidget(btn_cancel); footer.addWidget(btn_ok)
        root.addLayout(footer)

    def _accept(self):
        tipo = self.in_tipo.text().strip()
        nombre = self.in_nombre.text().strip()
        por_metro = self.in_por_metro.isChecked()
        maneja_stock = self.in_maneja_stock.isChecked()
        cantidad = int(self.in_cantidad.value()) if maneja_stock else 0

        if not tipo or not nombre:
            QMessageBox.warning(self, "Faltan datos", "Completá Tipo de módulo y Nombre.")
            return

        precio = 0.0 if por_metro else float(self.in_precio.value())

        # Guardamos ambos campos para compatibilidad: 'nombre' y 'material'
        self.data = {
            "tipo": tipo,
            "nombre": nombre,
            "material": nombre,     # compat con Presupuestador/Config
            "por_metro": por_metro,
            "precio": precio,
            "maneja_stock": maneja_stock,
            "cantidad": cantidad,
        }
        self.accept()

    def get_data(self):
        return self.data


# =========================
#       Cards base
# =========================
class AddCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, title="Nuevo", hint=None, emoji="➕"):
        super().__init__()
        self.setObjectName("AddCard")
        self.setCursor(Qt.PointingHandCursor)
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter)
        icon = QLabel(emoji); f = QFont(); f.setPointSize(42); f.setBold(True); icon.setFont(f); icon.setAlignment(Qt.AlignCenter)
        ttl = QLabel(title); ttl.setObjectName("CardTitle"); ttl.setAlignment(Qt.AlignCenter)
        v.addWidget(icon); v.addWidget(ttl)
        if hint:
            h = QLabel(hint); h.setObjectName("CardSubtitle"); v.addWidget(h)
    def mousePressEvent(self, e): self.clicked.emit()


class ModuleCard(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, nombre:str, count:int):
        super().__init__()
        self.setObjectName("ModuleCard")
        self.setCursor(Qt.PointingHandCursor)
        self.nombre = nombre
        v = QVBoxLayout(self); v.setAlignment(Qt.AlignCenter)
        icon = QLabel("🗂️"); f = QFont(); f.setPointSize(36); icon.setFont(f); icon.setAlignment(Qt.AlignCenter)
        ttl = QLabel(nombre); ttl.setObjectName("CardTitle"); ttl.setAlignment(Qt.AlignCenter)
        sub = QLabel(f"{count} producto(s)"); sub.setObjectName("CardSubtitle")
        v.addWidget(icon); v.addWidget(ttl); v.addWidget(sub)
    def mousePressEvent(self, e): self.clicked.emit(self.nombre)


class ProductCard(QFrame):
    editar = pyqtSignal(int)
    eliminar = pyqtSignal(int)

    def __init__(self, index:int, producto:dict):
        super().__init__()
        self.setObjectName("ProductCard")
        self.index = index
        self.producto = producto
        self.setCursor(Qt.PointingHandCursor)

        v = QVBoxLayout(self); v.setSpacing(6)

        # Header con título y badge de stock (si aplica)
        header = QHBoxLayout()
        header.setContentsMargins(0,0,0,0)

        title = QLabel(f"{producto.get('nombre') or producto.get('material')}")
        title.setObjectName("CardTitle")
        title.setAlignment(Qt.AlignLeft)

        header.addWidget(title)
        header.addStretch()

        if producto.get("maneja_stock", False):
            qty = int(producto.get("cantidad", 0))
            badge = QLabel(str(qty))
            badge.setObjectName("StockBadge")
            # estado dinámico para QSS
            badge.setProperty("stock", self._badge_state(qty))
            # refrescar estilos para que tome el property
            badge.style().unpolish(badge)
            badge.style().polish(badge)
            header.addWidget(badge, alignment=Qt.AlignRight)

        v.addLayout(header)

        price_txt = "Precio por metro" if producto.get("por_metro") else f"Precio: $ {producto.get('precio',0):,.2f}"
        subtitle = QLabel(price_txt); subtitle.setObjectName("CardSubtitle")
        v.addWidget(subtitle)

        actions = QHBoxLayout(); actions.addStretch()
        btn_edit = QPushButton("Editar"); btn_edit.setObjectName("ActionBtn")
        btn_del  = QPushButton("Eliminar"); btn_del.setObjectName("DangerBtn")
        btn_edit.clicked.connect(lambda: self.editar.emit(self.index))
        btn_del.clicked.connect(lambda: self.eliminar.emit(self.index))
        actions.addWidget(btn_edit); actions.addWidget(btn_del)
        v.addLayout(actions)

    def mousePressEvent(self, e):
        self.editar.emit(self.index)

    def _badge_state(self, qty: int) -> str:
        if qty <= 0:
            return "zero"
        if qty <= LOW_STOCK_THRESHOLD:
            return "low"
        return "ok"


# =========================
#     Vista Detalle Módulo
# =========================
class ModuleDetail(QWidget):
    """Pantalla que muestra productos de un módulo y permite alta/edición."""
    def __init__(self, parent, nombre_modulo: str):
        super().__init__(parent)
        self.parent_view = parent          # ProductosView
        self.nombre = nombre_modulo

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # Header local con Back
        header = QWidget(); header.setObjectName("ViewHeader")
        h = QHBoxLayout(header); h.setContentsMargins(0,0,8,8)
        back = QPushButton("← Módulos"); back.setObjectName("GhostBtn")
        back.clicked.connect(self._go_back)
        title = QLabel(self.nombre); title.setObjectName("HeaderTitle")
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(back); h.addSpacing(8); h.addWidget(title); h.addWidget(spacer)
        root.addWidget(header)

        # Buscador dentro del módulo por Nombre
        tools = QHBoxLayout()
        tools.addStretch()
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar por nombre…")
        self.search.textChanged.connect(self._refresh_grid)
        tools.addWidget(self.search)
        root.addLayout(tools)

        # Grid scroll
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setHorizontalSpacing(12); self.grid.setVerticalSpacing(12)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll)

        self._refresh_grid()

    # ---- Navegación ----
    def _go_back(self):
        self.parent_view._show_modules_home()

    # ---- Render productos ----
    def _refresh_grid(self):
        # limpiar
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.setParent(None)

        # Card "Nuevo producto"
        add = AddCard(title="Nuevo producto", hint=None, emoji="➕")
        try:
            from .ui_theme import apply_card_shadow
            apply_card_shadow(add)
        except Exception:
            pass
        add.clicked.connect(self._new_product)
        self.grid.addWidget(add, 0, 0)

        # productos del módulo actual
        productos = self.parent_view._modules.get(self.nombre, [])
        q = (self.search.text() or "").lower().strip()

        # visibles = [(idx_real, prod)]
        visibles = []
        for real_index, prod in enumerate(productos):
            nombre_busq = (prod.get("nombre") or prod.get("material") or "").lower()
            if not q or q in nombre_busq:
                visibles.append((real_index, prod))

        # pintar
        cols = 3
        for i_card, (real_index, prod) in enumerate(visibles):
            card = ProductCard(index=real_index, producto=prod)
            card.editar.connect(self._edit_product)
            card.eliminar.connect(self._delete_product)
            try:
                from .ui_theme import apply_card_shadow
                apply_card_shadow(card)
            except Exception:
                pass
            r, c = divmod(i_card + 1, cols)  # +1 por la card "Nuevo"
            self.grid.addWidget(card, r, c)

        # spacer
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        self.grid.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
                        self.grid.rowCount(), 0, 1, cols)

    # ---- Acciones producto ----
    def _new_product(self):
        dlg = ProductDialog(self, data=None, lock_tipo=True, fixed_tipo=self.nombre)
        if dlg.exec_() == QDialog.Accepted:
            self.parent_view._modules.setdefault(self.nombre, []).append(dlg.get_data())
            self._refresh_grid()
            self.parent_view._refresh_modules_home_counts()

    def _edit_product(self, idx: int):
        productos = self.parent_view._modules.get(self.nombre, [])
        current = dict(productos[idx])
        dlg = ProductDialog(self, data=current, lock_tipo=True, fixed_tipo=self.nombre)
        if dlg.exec_() == QDialog.Accepted:
            productos[idx] = dlg.get_data()
            self._refresh_grid()
            self.parent_view._refresh_modules_home_counts()

    def _delete_product(self, idx: int):
        productos = self.parent_view._modules.get(self.nombre, [])
        p = productos[idx]
        resp = QMessageBox.question(
            self, "Eliminar producto",
            f"¿Eliminar '{p.get('nombre')}' del módulo '{self.nombre}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            del productos[idx]
            self._refresh_grid()
            self.parent_view._refresh_modules_home_counts()


# =========================
#       Vista principal
# =========================
class ProductosView(QWidget):
    """
    Pantalla con dos niveles:
    1) Home de Módulos (cards + 'Nuevo módulo').
    2) Detalle de Módulo (productos + 'Nuevo producto').
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet(PRODUCTS_QSS)

        # Data en memoria: { nombre_modulo: [ {producto}, ... ] }
        self._modules = {}   # dict[str, list[dict]]

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Stacked interno
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # --- Vista 0: Home módulos ---
        self.modules_home = QWidget()
        mh_layout = QVBoxLayout(self.modules_home)
        mh_layout.setContentsMargins(0,0,0,0)
        mh_layout.setSpacing(8)

        header = QWidget(); header.setObjectName("ViewHeader")
        h = QHBoxLayout(header); h.setContentsMargins(0,0,8,8)
        title = QLabel("Módulos"); title.setObjectName("HeaderTitle")
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Buscador por módulo
        self.search_modules = QLineEdit(); self.search_modules.setPlaceholderText("Buscar módulo…")
        self.search_modules.textChanged.connect(self._paint_modules_grid)
        h.addWidget(title); h.addWidget(spacer); h.addWidget(self.search_modules)
        mh_layout.addWidget(header)

        self.modules_scroll = QScrollArea(); self.modules_scroll.setWidgetResizable(True)
        self.modules_container = QWidget()
        self.modules_grid = QGridLayout(self.modules_container)
        self.modules_grid.setContentsMargins(8, 8, 8, 8)
        self.modules_grid.setHorizontalSpacing(12); self.modules_grid.setVerticalSpacing(12)
        self.modules_scroll.setWidget(self.modules_container)
        mh_layout.addWidget(self.modules_scroll)

        self.stack.addWidget(self.modules_home)

        # --- Vista 1: Detalle de módulo (se inyecta dinámica) ---
        self.module_detail = None  # se creará al abrir un módulo

        # Pintar home al inicio
        self._paint_modules_grid()

    # ====== HOME MÓDULOS ======
    def _paint_modules_grid(self):
        # limpiar grid
        for i in reversed(range(self.modules_grid.count())):
            w = self.modules_grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        # Card "Nuevo módulo"
        add_card = AddCard(title="Nuevo módulo", hint=None, emoji="➕")
        try:
            from .ui_theme import apply_card_shadow
            apply_card_shadow(add_card)
        except Exception:
            pass
        self.modules_grid.addWidget(add_card, 0, 0)
        add_card.clicked.connect(self._new_module)

        # Construir lista visible (nombre_modulo, cantidad_productos)
        query = (self.search_modules.text() or "").lower().strip()
        visibles = []
        for mod_name, productos in (self._modules or {}).items():
            if not query or query in mod_name.lower():
                visibles.append((mod_name, len(productos)))

        # Orden alfabético
        visibles.sort(key=lambda t: t[0].lower())

        # Pintar cards
        cols = 3
        for idx, item in enumerate(visibles):
            mod_name, count = item  # 👈 nombres explícitos, sin 'nombre'
            card = ModuleCard(mod_name, count)
            try:
                from .ui_theme import apply_card_shadow
                apply_card_shadow(card)
            except Exception:
                pass
            card.clicked.connect(self._open_module)
            r, c = divmod(idx + 1, cols)  # +1 porque (0,0) es el "Nuevo módulo"
            self.modules_grid.addWidget(card, r, c)

        # Mensaje vacío (opcional)
        if not visibles and not query:
            empty = QLabel("Todavía no hay módulos. Creá el primero con “Nuevo módulo”.")
            empty.setObjectName("CardSubtitle")
            self.modules_grid.addWidget(empty, 1, 0, 1, cols)

        # Empujar todo hacia arriba
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        self.modules_grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding),
            self.modules_grid.rowCount(), 0, 1, cols
        )

    def _new_module(self):
        dlg = ModuleDialog(self, existentes=set(self._modules.keys()))
        if dlg.exec_() == QDialog.Accepted:
            nombre = dlg.get_nombre()
            if nombre:
                self._modules[nombre] = []
                self._paint_modules_grid()
                self._open_module(nombre)

    def _open_module(self, nombre: str):
        # Crear/Actualizar vista detalle y mostrar
        detail = ModuleDetail(self, nombre)
        if self.stack.count() == 1:
            self.stack.addWidget(detail)
        else:
            # reemplazar la vista detalle previa
            old = self.stack.widget(1)
            self.stack.removeWidget(old)
            old.deleteLater()
            self.stack.addWidget(detail)
        self.module_detail = detail
        self.stack.setCurrentIndex(1)

    def _show_modules_home(self):
        self.stack.setCurrentIndex(0)

    def _refresh_modules_home_counts(self):
        # Simplemente repintar el grid (actualiza contadores)
        if self.stack.currentIndex() == 0:
            self._paint_modules_grid()
        else:
            self._paint_modules_grid()  # para cuando volvés

    # ====== API pública ======
    def get_productos(self):
        """Devuelve todos los productos de todos los módulos (lista 'flat')."""
        flat = []
        for nombre, prods in self._modules.items():
            for p in prods:
                flat.append(p)
        return flat
    
    def refresh_open_module(self):
        """Refresca la vista actualmente abierta (home de módulos o detalle de módulo)."""
        # Actualiza contadores del home
        self._paint_modules_grid()
        # Si hay un módulo abierto, refresca su grilla
        if getattr(self, "module_detail", None) is not None:
            try:
                self.module_detail._refresh_grid()
            except Exception:
                pass
