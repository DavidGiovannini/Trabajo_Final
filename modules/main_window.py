from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton,
    QStackedWidget, QHBoxLayout, QSizePolicy, QFrame, QListWidget,
    QListWidgetItem, QGraphicsDropShadowEffect, QSpacerItem, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont

from .ui_theme import apply_card_shadow, add_hover_lift
from .productos_view import ProductosView
from .pedidos_view import PedidosView
from .configuracion_view import ConfiguracionView
from .presupuestador_view import PresupuestadorView


class SideButton(QPushButton):
    def __init__(self, text, on_click):
        super().__init__(text)
        self.setProperty("class", "SideBtn")
        self.setObjectName("")
        self.clicked.connect(on_click)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setProperty("active", "false")
    def setActive(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self); self.style().polish(self)


def _text_shadow(label, blur=8, dy=2, alpha=140):
    eff = QGraphicsDropShadowEffect(label)
    eff.setBlurRadius(blur); eff.setOffset(0, dy)
    c = QColor(0, 0, 0); c.setAlpha(alpha); eff.setColor(c)
    label.setGraphicsEffect(eff)


# ----------------- KPI -----------------
class StatPill(QFrame):
    FALLBACK_BG = {
        "KpiOlive":  "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8DA091, stop:1 #748B7D)",
        "KpiAmber":  "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #CBA866, stop:1 #B08C49)",
        "KpiIndigo": "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #879BB0, stop:1 #6E859A)",
        "KpiRed":    "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #C0837B, stop:1 #A16861)",
    }
    def __init__(self, title: str, value, variant: str, emoji: str = ""):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: 0;")
        self.setMinimumHeight(126)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.body = QFrame(self)
        self.body.setAttribute(Qt.WA_StyledBackground, True)
        self.body.setObjectName(variant)
        fb = self.FALLBACK_BG.get(variant, "")
        if fb:
            self.body.setStyleSheet(f"background:{fb}; border-radius:20px;")

        lay = QVBoxLayout(self.body)
        lay.setContentsMargins(18, 12, 18, 24); lay.setSpacing(0)

        headw = QWidget(self.body); headw.setAttribute(Qt.WA_StyledBackground, True)
        headw.setStyleSheet("background: transparent;")
        head = QHBoxLayout(headw); head.setContentsMargins(0,0,0,0); head.setSpacing(8)

        icon = QLabel(emoji or "")
        icon.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        icon.setStyleSheet("background:transparent; color:#FFFFFF; border:none;")
        ttl = QLabel(title); ttl.setWordWrap(True); ttl.setMinimumHeight(34)
        ttl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ttl.setStyleSheet("background:transparent; color:#FFFFFF; font-weight:800; border:none;")

        head.addWidget(icon, 0, Qt.AlignVCenter); head.addWidget(ttl, 1, Qt.AlignVCenter)

        val = QLabel(str(value))
        val.setStyleSheet("background:transparent; color:#FFFFFF; font-size:26px; font-weight:900;")

        _text_shadow(ttl, blur=6, dy=2, alpha=130)
        _text_shadow(val, blur=10, dy=2, alpha=160)

        lay.addWidget(headw)
        lay.addItem(QSpacerItem(0, 72, QSizePolicy.Minimum, QSizePolicy.Expanding))
        lay.addWidget(val, 0, Qt.AlignLeft | Qt.AlignBottom)

        warm = QGraphicsDropShadowEffect(self)
        warm.setBlurRadius(28); warm.setOffset(0, 10)
        col = QColor('#6E5A4A'); col.setAlpha(60); warm.setColor(col)
        self.setGraphicsEffect(warm)

    def resizeEvent(self, e):
        self.body.setGeometry(self.rect())
        super().resizeEvent(e)


# ----------------- Botones píldora -----------------
class PillButton(QPushButton):
    def __init__(self, emoji: str, title: str, variant: str):
        super().__init__(f"{emoji}  {title}")
        self.setObjectName("PillBtn")                 # <- clave para forzar la píldora
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)                       # altura estable => píldora perfecta
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFlat(True)

        # colores suaves por variante
        bg = {
            "green":  "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #C9D7BF, stop:1 #AFC9A3)",
            "sand":   "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F0E4D1, stop:1 #E4D6BE)",
            "orange": "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F3D1B7, stop:1 #E8BFA2)",
        }.get(variant, "#EFE7DB")

        # estilo inline que manda sobre cualquier regla genérica
        self.setStyleSheet(
            "QPushButton#PillBtn{"
            f"background:{bg};"
            "color:#2A2A2A; font-weight:900; text-align:left;"
            "padding:10px 18px;"
            "border:1px solid rgba(0,0,0,0.06);"
            "border-radius:999px;"              # <- redundante, pero asegura en runtime
            "}"
            "QPushButton#PillBtn:hover{filter:brightness(1.03);}"
            "QPushButton#PillBtn:pressed{transform:translateY(1px);}"
        )

        apply_card_shadow(self, blur=16, dy=7, alpha=85)
        add_hover_lift(self)


# ----------------- Badges píldora -----------------
class PillBadge(QLabel):
    def __init__(self, text: str, variant: str, fixed_w: int = None):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(26)                      # altura consistente
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAttribute(Qt.WA_StyledBackground, True)

        if variant == "yellow":   # Pendiente
            css = "background:#F5E6A3; color:#1F2937; border:1px solid rgba(0,0,0,.10);"
        elif variant == "green":  # Aprobado
            css = "background:#BFE8C7; color:#10341F; border:1px solid rgba(0,0,0,.10);"
        else:                     # Enviado
            css = "background:#C9CED6; color:#0F172A; border:1px solid rgba(0,0,0,.10);"

        # píldora real
        self.setStyleSheet(
            "border-radius:13px; padding:4px 12px; font-weight:700; " + css
        )

        if fixed_w is not None:
            self.setFixedWidth(fixed_w)

# ----------------- Home -----------------
class HomeDashboard(QWidget):
    def __init__(self, on_new_presu, on_new_pedido, on_add_material):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        area = QWidget(); area.setObjectName("WarmDash")
        grid = QGridLayout(area)
        grid.setContentsMargins(16,8,16,12)
        grid.setHorizontalSpacing(8); grid.setVerticalSpacing(12)
        for c in range(4): grid.setColumnStretch(c, 1)
        root.addWidget(area)

        # KPIs
        grid.addWidget(StatPill("Presupuestos", 3, "KpiOlive",  "📋"), 0, 0)
        grid.addWidget(StatPill("Pedidos pendientes", 5, "KpiAmber", "⏱"), 0, 1)
        grid.addWidget(StatPill("En producción", 2, "KpiIndigo", "🏭"), 0, 2)
        grid.addWidget(StatPill("Pendiente actualización", 7, "KpiRed", "🧱"), 0, 3)

        # Botonera 2×2 (píldoras) – misma columna de la tabla
        buttons_wrap = QFrame(); buttons_wrap.setObjectName("SectionCard")
        bw = QGridLayout(buttons_wrap); 
        bw.setContentsMargins(12,12,12,12); 
        bw.setHorizontalSpacing(16); 
        bw.setVerticalSpacing(10)
        b1 = PillButton("➕", "Nuevo Presupuesto", "sand");   b1.clicked.connect(on_new_presu)
        b2 = PillButton("📦", "Agregar Material",   "sand");    b2.clicked.connect(on_add_material)
        b3 = PillButton("🧾", "Nuevo Pedido",       "sand");    b3.clicked.connect(on_new_pedido)
        b4 = PillButton("⬆️", "Actualizar precios (%)", "sand"); b4.clicked.connect(on_add_material)
        bw.addWidget(b1, 0, 0); bw.addWidget(b2, 0, 1)
        bw.addWidget(b3, 1, 0); bw.addWidget(b4, 1, 1)
        grid.addWidget(buttons_wrap, 1, 0, 1, 2)

        # IZQUIERDA: Últimos presupuestos (ancha)
        left_card = QFrame(); left_card.setObjectName("SectionCard")
        left_lay = QVBoxLayout(left_card); left_lay.setContentsMargins(12,12,12,12); left_lay.setSpacing(8)
        t_left = QLabel("Últimos presupuestos"); t_left.setObjectName("SectionTitle")
        left_lay.addWidget(t_left)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("UltimosPresTable")
        self.table.setHorizontalHeaderLabels(["Cliente", "Total", "Fecha", "Estado"])
        self.table.setStyleSheet(
            "QTableWidget#UltimosPresTable{background:#FFF9F0; color:#1C1E22; border:none; border-radius:12px;}"
            "QTableWidget#UltimosPresTable::item{color:#1C1E22;}"
        )
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        left_lay.addWidget(self.table)

        # DERECHA: Pedidos Pendientes
        right_top = QFrame();  right_top.setObjectName("SectionCard")
        rt_lay = QVBoxLayout(right_top); rt_lay.setContentsMargins(12,12,12,12); rt_lay.setSpacing(8)
        t_rt = QLabel("Pedidos Pendientes"); t_rt.setObjectName("SectionTitle")
        rt_lay.addWidget(t_rt)
        self.pend_list = QListWidget(); self.pend_list.setFrameShape(QFrame.NoFrame)
        self.pend_list.setStyleSheet("QListWidget{background:transparent;} QListWidget::item{padding:6px 8px; border-radius:8px; color:#2A2A2A;} QListWidget::item:hover{background:#F4EEE6;}")
        for p in ("#1104 Arq. López — 3 días más", "#98 Sra. González — 2 días atrasado", "#95 Martinez Muebles — 2 días más"):
            self.pend_list.addItem(QListWidgetItem(p))
        rt_lay.addWidget(self.pend_list)

        # DERECHA ABAJO: Alertas
        right_bottom = QFrame(); right_bottom.setObjectName("SectionCard")
        rb_lay = QVBoxLayout(right_bottom); rb_lay.setContentsMargins(12,12,12,12); rb_lay.setSpacing(8)
        t_rb = QLabel("Alertas"); t_rb.setObjectName("SectionTitle")
        rb_lay.addWidget(t_rb)
        self.alert_list = QListWidget(); self.alert_list.setFrameShape(QFrame.NoFrame)
        self.alert_list.setStyleSheet("QListWidget{background:transparent;} QListWidget::item{padding:6px 8px; border-radius:8px; color:#2A2A2A;} QListWidget::item:hover{background:#F4EEE6;}")
        for a in ("Melamina Blanca 18mm sin precio", "Herrajes subieron hace 45 días", "Pedido #104 vence mañana"):
            self.alert_list.addItem(QListWidgetItem(a))
        rb_lay.addWidget(self.alert_list)

        grid.addWidget(left_card,   2, 0, 2, 2)
        grid.addWidget(right_top,   2, 2, 1, 2)
        grid.addWidget(right_bottom,3, 2, 1, 2)

        self._seed_demo_rows()

    def _seed_demo_rows(self):
        from PyQt5.QtGui import QFont

        data = [
            ("Sra. González", "$105.000", "24-04-2024", "Pendiente"),
            ("Arq. López",    "$72.500",  "22-04-2024", "Aprobado"),
            ("Sr. Martínez",  "$145.000", "18-04-2024", "Enviado"),
        ]

        # --- Ancho máximo de las píldoras ---
        test_badges = [
            PillBadge("Pendiente", "yellow"),
            PillBadge("Aprobado",  "green"),
            PillBadge("Enviado",   "gray"),
        ]
        max_pill_w = max(b.sizeHint().width() for b in test_badges) + 6

        for cliente, total, fecha, estado in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 32)

            # Cliente
            it_cliente = QTableWidgetItem(cliente)
            it_cliente.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(r, 0, it_cliente)

            # Total: izquierda + negrita (para que TODOS arranquen en la misma columna)
            it_total = QTableWidgetItem(total)
            it_total.setFlags(Qt.ItemIsEnabled)
            it_total.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            f = QFont(self.table.font()); f.setBold(True)
            it_total.setFont(f)
            self.table.setItem(r, 1, it_total)

            # Fecha centrada
            it_fecha = QTableWidgetItem(fecha)
            it_fecha.setFlags(Qt.ItemIsEnabled)
            it_fecha.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, it_fecha)

            # Badge según estado (mismo ancho y borde hiper-redondeado)
            est = estado.lower()
            if "pend" in est:
                badge = PillBadge("Pendiente", "yellow")
            elif "aprob" in est:
                badge = PillBadge("Aprobado", "green")
            else:
                badge = PillBadge("Enviado", "gray")

            badge.setFixedHeight(24)
            badge.setFixedWidth(max_pill_w)
            # refuerzo del borde redondeado por si un tema lo aplana
            badge.setStyleSheet(badge.styleSheet() + "border-radius:999px; padding:3px 10px; background-clip: padding;")

            # Celda transparente y CENTRADA
            cell = QWidget(); cell.setAttribute(Qt.WA_StyledBackground, True)
            cell.setStyleSheet("background: transparent;")
            from PyQt5.QtWidgets import QHBoxLayout
            hl = QHBoxLayout(cell)
            hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(0)
            hl.addStretch(1); hl.addWidget(badge, 0, Qt.AlignVCenter); hl.addStretch(1)
            self.table.setCellWidget(r, 3, cell)

        # Anchos de columnas (cliente se estira; total/fecha fijos; estado por píldora)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)

        fm = self.table.fontMetrics()
        w_total  = fm.horizontalAdvance("$145.000") + 24
        w_fecha  = fm.horizontalAdvance("24-04-2024") + 24
        w_estado = max_pill_w + 24

        self.table.setColumnWidth(1, w_total)
        self.table.setColumnWidth(2, w_fecha)
        self.table.setColumnWidth(3, w_estado)
    
    def update_presupuestos(self, rows):

        self.table.setRowCount(0)

        # --- preparar badges para calcular ancho máximo según los estados que vengan ---
        def make_badge(text, variant):
            b = PillBadge(text, variant)
            # refuerzo runtime por si el tema del SO aplanara bordes
            b.setStyleSheet(b.styleSheet() + "border-radius:999px; padding:3px 10px; background-clip: padding;")
            b.setFixedHeight(24)
            return b

        # map simple por estado (extensible)
        def badge_for(estado_texto: str):
            est = (estado_texto or "").strip().lower()
            if "pend" in est:  return make_badge("Pendiente", "yellow")
            if "aprob" in est: return make_badge("Aprobado", "green")
            return make_badge("Enviado", "gray")

        # construir todos los badges para medir ancho máximo real
        badges = [badge_for(r[3]) for r in rows]
        max_pill_w = (max((b.sizeHint().width() for b in badges), default=80)) + 6

        # fuente para totales en negrita
        f_bold = QFont(self.table.font())
        f_bold.setBold(True)

        # cargar filas
        for i, (cliente, total, fecha, estado) in enumerate(rows):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 32)

            it_cliente = QTableWidgetItem(cliente); it_cliente.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, it_cliente)

            it_total = QTableWidgetItem(total); it_total.setFlags(Qt.ItemIsEnabled)
            it_total.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it_total.setFont(f_bold)
            self.table.setItem(i, 1, it_total)

            it_fecha = QTableWidgetItem(fecha); it_fecha.setFlags(Qt.ItemIsEnabled)
            it_fecha.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, it_fecha)

            badge = badge_for(estado)
            badge.setFixedWidth(max_pill_w)

            cell = QWidget(); cell.setAttribute(Qt.WA_StyledBackground, True)
            cell.setStyleSheet("background: transparent;")
            hl = QHBoxLayout(cell); hl.setContentsMargins(0,0,0,0); hl.setSpacing(0)
            hl.addStretch(1); hl.addWidget(badge, 0, Qt.AlignVCenter); hl.addStretch(1)
            self.table.setCellWidget(i, 3, cell)

        # --- ajustar anchos de columnas en función del contenido actual ---
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)       # Cliente se estira
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)   # Total fijo
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)   # Fecha fija
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)         # Estado por píldora

        fm = self.table.fontMetrics()
        # el ancho del total lo tomamos del mayor string que veas posible (con margen)
        widest_total = max((len(t or "") for _, t, *_ in rows), default=8)
        sample_total = "$" + "9" * max(7, widest_total - 1)
        w_total  = fm.horizontalAdvance(sample_total) + 24
        # fecha con patrón dd-mm-aaaa
        w_fecha  = fm.horizontalAdvance("24-04-2024") + 24
        w_estado = max_pill_w + 24

        self.table.setColumnWidth(1, w_total)
        self.table.setColumnWidth(2, w_fecha)
        self.table.setColumnWidth(3, w_estado)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Pedidos - Muebles a Medida")
        self.resize(1200, 760)

        center = QWidget()
        center_l = QHBoxLayout(center); center_l.setContentsMargins(0, 0, 0, 0); center_l.setSpacing(0)
        sidebar = self._build_sidebar(); center_l.addWidget(sidebar)

        self.stack = QStackedWidget(); center_l.addWidget(self.stack, 1)
        self.setCentralWidget(center)

        self.view_productos = ProductosView()
        self.view_pedidos = PedidosView()
        self.view_config = ConfiguracionView()
        self.view_presu = PresupuestadorView(self.view_productos, self.view_pedidos, self.view_config)

        self.home = HomeDashboard(
            on_new_presu=self._show_presu,
            on_new_pedido=self._show_pedidos,
            on_add_material=self._show_config
        )

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.view_presu)
        self.stack.addWidget(self.view_productos)
        self.stack.addWidget(self.view_config)
        self.stack.addWidget(self.view_pedidos)

        self._activate("inicio")

    def _build_sidebar(self) -> QWidget:
        side = QWidget(); side.setObjectName("Sidebar")
        from PyQt5.QtWidgets import QVBoxLayout
        lay = QVBoxLayout(side); lay.setContentsMargins(10,10,10,10); lay.setSpacing(6)

        logo = QLabel("🪑  MUEBLES\nA MEDIDA"); logo.setObjectName("SideLogo"); lay.addWidget(logo)

        self.btn_inicio = SideButton("Inicio", lambda: self._goto(0, "inicio"))
        self.btn_presu  = SideButton("Presupuestador", lambda: self._goto(1, "presu"))
        self.btn_prod   = SideButton("Productos",      lambda: self._goto(2, "prod"))
        self.btn_mat    = SideButton("Materiales",     lambda: self._goto(3, "mat"))
        self.btn_ped    = SideButton("Pedidos",        lambda: self._goto(4, "ped"))
        self.btn_cfg    = SideButton("Ajustes",        lambda: self._goto(3, "mat"))
        for b in (self.btn_inicio, self.btn_presu, self.btn_prod, self.btn_mat, self.btn_ped, self.btn_cfg):
            b.setMinimumWidth(160); lay.addWidget(b)

        lay.addStretch()
        user = QLabel("S. Valvo"); user.setStyleSheet("padding:8px 12px; color:#9AA3B2;")
        lay.addWidget(user)
        return side

    def _goto(self, index: int, key: str):
        self.stack.setCurrentIndex(index); self._activate(key)

    def _activate(self, key: str):
        for k, btn in {
            "inicio": self.btn_inicio, "presu": self.btn_presu, "prod": self.btn_prod,
            "mat": self.btn_mat, "ped": self.btn_ped, "cfg": self.btn_cfg
        }.items():
            btn.setActive(k == key)

    def _show_presu(self): self._goto(1, "presu")
    def _show_productos(self): self._goto(2, "prod")
    def _show_config(self): self._goto(3, "mat")
    def _show_pedidos(self): self._goto(4, "ped")