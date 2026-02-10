import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from modules.ui_theme import THEME_QSS
from modules.main_window import MainWindow

def main():
    # HiDPI (opcional)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # ❗ Aplica el QSS TAL CUAL, sin reemplazos de iconos ni recursos
    app.setStyleSheet(THEME_QSS)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

