from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget,
    QCheckBox, QScrollArea, QGroupBox, QFormLayout, QMessageBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QDoubleSpinBox, QFrame
)
from .ui_theme import apply_card_shadow
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap
import os

def money(n):
    return f"${n:,.2f}"

class PresupuestadorView(QWidget):
    # >>> Señal para actualizar el panel de “Últimos presupuestos”
    presupuestos_changed = pyqtSignal(list)

    def __init__(self, productos_view, pedidos_view, configuracion_view):
        super().__init__()
        self.productos_view = productos_view
        self.pedidos_view = pedidos_view
        self.config_view = configuracion_view

        # historial simple de presupuestos mostrados en el dashboard
        self._hist_presup = []  # [{cliente,total,fecha,estado}]

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # ---- Tabs de módulos (cada form_group llevará sombra) ----
        self.tabs_modulos = QTabWidget()
        root.addWidget(self.tabs_modulos)

        # ---- Card de resumen (Total + tabla + botones) ----
        self.summary_card = QFrame()
        self.summary_card.setObjectName("ProductCard")
        apply_card_shadow(self.summary_card, blur=20, dx=0, dy=12, alpha=110)
        s_lay = QVBoxLayout(self.summary_card)
        s_lay.setContentsMargins(12, 12, 12, 12)
        s_lay.setSpacing(10)

        self.total_label = QLabel("Total: $0")
        self.total_label.setAlignment(Qt.AlignRight)
        s_lay.addWidget(self.total_label)

        self.tabla_resumen = QTableWidget(0, 3)
        self.tabla_resumen.setHorizontalHeaderLabels(["Producto", "Cantidad/Metros", "Subtotal"])
        self.tabla_resumen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        s_lay.addWidget(self.tabla_resumen)

        button_layout = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar productos")
        self.btn_calcular   = QPushButton("Calcular presupuesto")
        self.btn_cargar_pedido = QPushButton("Cargar pedido")
        self.btn_cargar_pedido.setObjectName("PrimaryBtn")
        self.btn_cargar_pedido.setEnabled(False)
        self.btn_actualizar.clicked.connect(self.cargar_modulos)
        self.btn_calcular.clicked.connect(self.calcular_total)
        self.btn_cargar_pedido.clicked.connect(self.popup_cargar_pedido)

        button_layout.addWidget(self.btn_actualizar)
        button_layout.addWidget(self.btn_calcular)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cargar_pedido)
        s_lay.addLayout(button_layout)

        root.addWidget(self.summary_card)

        # Estado interno
        self.productos_widgets = []
        self.cargar_modulos()

        # Cargar demo inicial para que el dashboard no quede vacío
        self._seed_demo()

    def _seed_demo(self):
        if not self._hist_presup:
            self._hist_presup = [
                {"cliente":"Sra. González","total":105000,"fecha":"24-04-2024","estado":"pendiente"},
                {"cliente":"Arq. López","total":72500,"fecha":"22-04-2024","estado":"aprobado"},
                {"cliente":"Sr. Martinez","total":145000,"fecha":"18-04-2024","estado":"enviado"},
            ]
            self.presupuestos_changed.emit(self._hist_presup)

    def cargar_modulos(self):
        self.tabs_modulos.clear()
        self.productos_widgets = []
        self.tabla_resumen.setRowCount(0)
        self.total_label.setText("Total: $0")
        self.btn_cargar_pedido.setEnabled(False)

        productos = self.productos_view.get_productos()
        if not productos:
            QMessageBox.information(self, "Sin productos", "No hay productos cargados.")
            return

        # Agrupar por tipo (módulo)
        modulos = {}
        for prod in productos:
            modulos.setdefault(prod['tipo'], []).append(prod)

        for tipo, lista_productos in modulos.items():
            tab = QWidget()
            layout_tab = QVBoxLayout(tab)
            layout_tab.setContentsMargins(6, 6, 6, 6)
            layout_tab.setSpacing(6)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)

            # group como card con sombra
            form_group  = QGroupBox(f"{tipo}")
            form_layout = QFormLayout()
            form_group.setLayout(form_layout)
            apply_card_shadow(form_group, blur=16, dx=0, dy=8, alpha=90)

            # Contenido
            for producto in lista_productos:
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(8)

                checkbox = QCheckBox(f"{producto.get('nombre') or producto.get('material')}")
                spinbox = QSpinBox()
                spinbox.setMinimum(1)
                spinbox.setValue(1)
                spinbox.setEnabled(False)

                metrosbox = QDoubleSpinBox()
                metrosbox.setSuffix(" m")
                metrosbox.setDecimals(2)
                metrosbox.setMinimum(0.10)
                metrosbox.setValue(1.00)
                metrosbox.setEnabled(False)

                por_metro = producto.get("por_metro", False)

                checkbox.toggled.connect(spinbox.setEnabled)
                checkbox.toggled.connect(metrosbox.setEnabled)

                container_layout.addWidget(checkbox)

                if por_metro:
                    container_layout.addWidget(QLabel("Metros:"))
                    container_layout.addWidget(metrosbox)
                    container_layout.addSpacing(8)
                    container_layout.addWidget(QLabel("Cant.:"))
                    container_layout.addWidget(spinbox)
                else:
                    container_layout.addWidget(QLabel("Cantidad:"))
                    container_layout.addWidget(spinbox)

                form_layout.addRow(container)
                self.productos_widgets.append((checkbox, spinbox, metrosbox, producto))

            scroll.setWidget(form_group)
            layout_tab.addWidget(scroll)
            self.tabs_modulos.addTab(tab, tipo)

    def calcular_total(self):
        precios_metro = self.config_view.get_precios_por_metro()
        total = 0.0
        self.tabla_resumen.setRowCount(0)

        for checkbox, spinbox, metrosbox, producto in self.productos_widgets:
            if not checkbox.isChecked():
                continue

            cant   = int(spinbox.value())
            metros = float(metrosbox.value())
            if producto.get("por_metro", False):
                precio = float(precios_metro.get(producto["material"], 0))
                subtotal = cant * metros * precio
                desc = f"{producto['tipo']} - {producto['material']} ({metros:.2f} m x {money(precio)})"
                cantidad_txt = f"{metros:.2f} m (x{cant})"
            else:
                precio = float(producto.get("precio", 0))
                subtotal = cant * precio
                desc = f"{producto['tipo']} - {producto['material']} ({money(precio)})"
                cantidad_txt = f"{cant}"

            row = self.tabla_resumen.rowCount()
            self.tabla_resumen.insertRow(row)
            self.tabla_resumen.setItem(row, 0, QTableWidgetItem(desc))
            self.tabla_resumen.setItem(row, 1, QTableWidgetItem(cantidad_txt))
            self.tabla_resumen.setItem(row, 2, QTableWidgetItem(money(subtotal)))
            total += subtotal

        self.total_label.setText(f"Total: {money(total)}")
        self.btn_cargar_pedido.setEnabled(self.tabla_resumen.rowCount() > 0)

    def popup_cargar_pedido(self):
        # Construir resumen desde la tabla ya calculada
        resumen = []
        total   = 0.0
        for row in range(self.tabla_resumen.rowCount()):
            desc = self.tabla_resumen.item(row, 0).text()
            cant = self.tabla_resumen.item(row, 1).text()
            sub  = self.tabla_resumen.item(row, 2).text()
            resumen.append(f"{desc} • {cant} → {sub}")
            total += float(sub.replace("$", "").replace(",", ""))

        dialog = PedidoDialog(total, resumen, self)
        if dialog.exec_() == QDialog.Accepted:
            datos = dialog.resultado

            # 1) Descontar stock
            advertencias = self._aplicar_descuento_stock()

            # 2) Cargar pedido a la lista
            self.pedidos_view.agregar_pedido(
                datos["cliente"], datos["telefono"], resumen, total
            )

            # >>> 3) Registrar presupuesto en el historial (marcamos como “enviado”)
            fecha_str = QDate.currentDate().toString("dd-MM-yyyy")
            self._hist_presup.insert(0, {
                "cliente": datos["cliente"],
                "total": total,
                "fecha": fecha_str,
                "estado": "enviado"
            })
            # mantener últimos 10
            self._hist_presup = self._hist_presup[:10]
            self.presupuestos_changed.emit(self._hist_presup)

            # 4) Avisos de stock
            if advertencias:
                QMessageBox.warning(self, "Stock actualizado con advertencias", advertencias)
            else:
                QMessageBox.information(self, "Pedido cargado", "El pedido fue cargado y el stock se actualizó.")

            # 5) Refrescar UI de Productos (badges, contadores)
            self._refresh_productos_ui()

            # 6) Deshabilitar botón hasta recalcular
            self.btn_cargar_pedido.setEnabled(False)

    # ---------- Stock ----------
    def _aplicar_descuento_stock(self) -> str:
        agotados = []
        negativos = []

        for checkbox, spinbox, metrosbox, producto in self.productos_widgets:
            if not checkbox.isChecked():
                continue
            if not producto.get("maneja_stock", False):
                continue

            cant_pedida = int(spinbox.value())
            actual = int(producto.get("cantidad", 0))
            nuevo = actual - cant_pedida
            producto["cantidad"] = nuevo

            nombre = producto.get("nombre") or producto.get("material")
            tipo   = producto.get("tipo", "")

            if nuevo < 0:
                negativos.append(f"• {nombre} ({tipo}) — {actual} → {nuevo}")
            elif nuevo == 0:
                agotados.append(f"• {nombre} ({tipo}) — {actual} → {nuevo}")

        msgs = []
        if negativos:
            msgs.append("Quedaron con stock NEGATIVO:\n" + "\n".join(negativos))
        if agotados:
            msgs.append("\nSe quedaron SIN stock:\n" + "\n".join(agotados))

        return "\n\n".join(msgs).strip()

    def _refresh_productos_ui(self):
        if hasattr(self.productos_view, "refresh_open_module"):
            try:
                self.productos_view.refresh_open_module()
            except Exception:
                pass
        if hasattr(self.productos_view, "_refresh_modules_home_counts"):
            try:
                self.productos_view._refresh_modules_home_counts()
            except Exception:
                pass


class PedidoDialog(QDialog):
    def __init__(self, total, resumen, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Datos del pedido")
        self.resultado = None

        layout = QVBoxLayout(self)
        self.cliente  = QLineEdit()
        self.telefono = QLineEdit()

        layout.addWidget(QLabel("Cliente:"))
        layout.addWidget(self.cliente)
        layout.addWidget(QLabel("Teléfono:"))
        layout.addWidget(self.telefono)
        layout.addWidget(QLabel("Resumen:"))
        for linea in resumen:
            layout.addWidget(QLabel(f"• {linea}"))
        layout.addWidget(QLabel(f"Total: {money(total)}"))

        btn_guardar = QPushButton("Guardar pedido")
        btn_guardar.setObjectName("PrimaryBtn")
        btn_guardar.clicked.connect(self.aceptar)
        layout.addWidget(btn_guardar)

    def aceptar(self):
        if not self.cliente.text().strip() or not self.telefono.text().strip():
            QMessageBox.warning(self, "Faltan datos", "Completá todos los campos.")
            return
        self.resultado = {"cliente": self.cliente.text().strip(), "telefono": self.telefono.text().strip()}
        self.accept()