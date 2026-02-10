from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QCheckBox, QPushButton, QSizePolicy, QHeaderView
from PyQt5.QtCore import Qt
from .ui_theme import apply_card_shadow


class ConfiguracionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ---------- Barra superior con checkbox maestro ----------
        topbar = QHBoxLayout()
        topbar.setContentsMargins(0, 0, 0, 0)
        topbar.setSpacing(8)

        self.chk_master = QCheckBox("Seleccionar todo")
        # (toma el estilo del theme: borde verde y tilde)
        self.chk_master.stateChanged.connect(self._on_master_toggled)
        topbar.addWidget(self.chk_master)
        topbar.addStretch()
        root.addLayout(topbar)

        # ---------- Tabla ----------
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)  # [0]=✓, [1]=Material, [2]=Precio por metro
        self.table.setHorizontalHeaderLabels(["", "Material", "Precio"])
        self.table.verticalHeader().setVisible(True)   # números de fila (si no querés, poné False)
        self.table.setCornerButtonEnabled(False)       # <- SACA el cuadrado blanco
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(False)

        # ancho fijo para la columna de checks
        self.table.setColumnWidth(0, 36)
        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)  # que la última NO se estire
        hh.setSectionResizeMode(0, QHeaderView.Fixed)            # ✓ fija
        hh.setSectionResizeMode(1, QHeaderView.Stretch)          # Material ocupa lo que queda
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        root.addWidget(self.table)

        # ---------- Botonera inferior (dejá la tuya si ya existe) ----------
        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Agregar fila", objectName="GhostBtn"))
        btns.addWidget(QPushButton("Eliminar fila", objectName="GhostBtn"))
        btns.addStretch()
        btns.addWidget(QPushButton("Guardar cambios", objectName="PrimaryBtn"))
        root.addLayout(btns)

        # Cargar datos iniciales (si ya tenías un método, llamalo acá)
        self._load_data()

    # ----------------- Lógica -----------------
    def _load_data(self):
        """
        Cargá tus datos reales aquí. Dejo ejemplo con lista.
        Si ya tenías datos, reemplazá esta parte por tu lógica.
        """
        data = [
            ("Melamina", 7000.0),
            ("Chapa MDF", 6800.0),
            ("Melamina premium", 8500.0),
        ]
        self.table.setRowCount(len(data))
        for r, (mat, precio) in enumerate(data):
            # Columna 0: checkbox por fila
            chk = QCheckBox()
            # centrado
            w = QWidget()
            lay = QHBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.addStretch(); lay.addWidget(chk); lay.addStretch()
            self.table.setCellWidget(r, 0, w)

            # Columna 1: material
            item_mat = QTableWidgetItem(mat)
            self.table.setItem(r, 1, item_mat)

            # Columna 2: precio por metro
            item_precio = QTableWidgetItem(f"{precio:.1f}")
            item_precio.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 2, item_precio)

    def _iter_row_checks(self):
        """Genera los QCheckBox de cada fila (columna 0)."""
        rows = self.table.rowCount()
        for r in range(rows):
            w = self.table.cellWidget(r, 0)
            if not w: 
                continue
            # el checkbox está dentro de un widget contenedor
            chk = w.findChild(QCheckBox)
            if chk:
                yield chk

    def _on_master_toggled(self, state):
        """Tilda/destilda todos los checks de la primera columna."""
        checked = (state == Qt.Checked)
        for chk in self._iter_row_checks():
            chk.blockSignals(True)
            chk.setChecked(checked)
            chk.blockSignals(False)