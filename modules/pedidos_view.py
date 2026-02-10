from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QMessageBox, QFrame
from PyQt5.QtCore import Qt
from .ui_theme import apply_card_shadow

class PedidosView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pedidos")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # --- Card contenedora de las dos columnas ---
        self.card = QFrame()
        self.card.setObjectName("ProductCard")  # reutiliza estilo de card del theme
        apply_card_shadow(self.card, blur=20, dx=0, dy=12, alpha=110)

        cont_layout = QHBoxLayout(self.card)
        cont_layout.setContentsMargins(12, 12, 12, 12)
        cont_layout.setSpacing(12)

        # Columnas como "subcards"
        self.col_en_curso = QFrame()
        self.col_en_curso.setObjectName("ProductCard")
        apply_card_shadow(self.col_en_curso, blur=16, dx=0, dy=8, alpha=90)
        col1 = QVBoxLayout(self.col_en_curso)
        col1.setContentsMargins(10, 10, 10, 10)
        col1.setSpacing(8)

        self.col_finalizados = QFrame()
        self.col_finalizados.setObjectName("ProductCard")
        apply_card_shadow(self.col_finalizados, blur=16, dx=0, dy=8, alpha=90)
        col2 = QVBoxLayout(self.col_finalizados)
        col2.setContentsMargins(10, 10, 10, 10)
        col2.setSpacing(8)

        # Listas
        self.pedidos_en_curso = QListWidget()
        self.pedidos_finalizados = QListWidget()

        for lw in (self.pedidos_en_curso, self.pedidos_finalizados):
            lw.setAcceptDrops(True)
            lw.setDragEnabled(True)
            lw.setDragDropMode(QListWidget.InternalMove)
            lw.setSelectionMode(QListWidget.SingleSelection)
            lw.setContextMenuPolicy(Qt.CustomContextMenu)
            lw.customContextMenuRequested.connect(self._menu_contextual)

        # Títulos y armado
        t1 = QLabel("En curso");  t1.setObjectName("CardTitle")
        t2 = QLabel("Finalizados"); t2.setObjectName("CardTitle")

        col1.addWidget(t1)
        col1.addWidget(self.pedidos_en_curso)

        col2.addWidget(t2)
        col2.addWidget(self.pedidos_finalizados)

        cont_layout.addWidget(self.col_en_curso, 1)
        cont_layout.addWidget(self.col_finalizados, 1)

        root.addWidget(self.card)

    def agregar_pedido(self, cliente, telefono, resumen, total):
        texto = f"{cliente} ({telefono})\n" + "\n".join(resumen) + f"\nTOTAL: ${total:,.2f}"
        item = QListWidgetItem(texto)
        item.setData(Qt.UserRole, {"cliente": cliente, "telefono": telefono, "resumen": resumen, "total": total})
        self.pedidos_en_curso.addItem(item)

    # Menú contextual: finalizar/restaurar/ver/eliminar
    def _menu_contextual(self, pos):
        sender = self.sender()
        item = sender.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole) or {}

        menu = QMenu(self)
        if sender is self.pedidos_en_curso:
            act_toggle = menu.addAction("Marcar como finalizado")
        else:
            act_toggle = menu.addAction("Restaurar a En curso")
        act_ver = menu.addAction("Ver detalle")
        menu.addSeparator()
        act_del = menu.addAction("Eliminar")

        act = menu.exec_(sender.mapToGlobal(pos))
        if not act:
            return

        if act == act_toggle:
            self._mover_item(item, destino=self.pedidos_finalizados if sender is self.pedidos_en_curso else self.pedidos_en_curso)
        elif act == act_ver:
            detalle = f"Cliente: {data.get('cliente')}\nTeléfono: {data.get('telefono')}\n\n" + "\n".join(data.get("resumen", [])) + f"\n\nTOTAL: ${data.get('total', 0):,.2f}"
            QMessageBox.information(self, "Detalle de pedido", detalle)
        elif act == act_del:
            fila = sender.row(item)
            sender.takeItem(fila)

    def _mover_item(self, item, destino):
        # Clonar y mover
        nuevo = QListWidgetItem(item.text())
        nuevo.setData(Qt.UserRole, item.data(Qt.UserRole))
        destino.addItem(nuevo)
        lista_origen = self.pedidos_en_curso if destino is self.pedidos_finalizados else self.pedidos_finalizados
        lista_origen.takeItem(lista_origen.row(item))