import os
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QFile

# check opcional (no loguea si no existe)
_CHECK_RES = ':/icons/check_white.svg'
_HAS_CHECK = QFile(_CHECK_RES).exists()
_CHECK_IMAGE_LINE = f"image: url({_CHECK_RES});" if _HAS_CHECK else ""

THEME_QSS = f"""
/* ===== BASE ===== */
QWidget {{
    background: qlineargradient(x1:0,y1:0, x2:1,y2:1, stop:0 #0e1116, stop:1 #141922);
    color: #E6E8EC;
    font-size: 13px;
}}
QLabel {{ background: transparent; color: #E6E8EC; }}

/* ===== Cards (módulos oscuros) ===== */
#MenuCard, #ProductCard, #AddCard, #ModuleCard {{
    background: #1b202a;
    border: 1px solid rgba(230,232,236,0.10);
    border-radius: 18px;
    padding: 20px;
}}
#MenuCard:hover, #ProductCard:hover, #AddCard:hover, #ModuleCard:hover {{
    border-color: #6ea8fe;
    background: #1e2430;
}}

/* Botones base (no afecta a la botonera cálida) */
QPushButton {{
    background: #2a3342; color: #E6E8EC;
    padding: 8px 14px; border-radius: 12px; border: 1px solid rgba(230,232,236,0.10);
    font-weight: 600;
}}
QPushButton:hover {{ background: #323c4e; }}
#PrimaryBtn {{ background: #6ea8fe; color: #0b1020; border: none; font-weight: 800; }}
#PrimaryBtn:hover {{ background: #8bb9ff; }}
#GhostBtn   {{ background: transparent; border: 1px solid rgba(230,232,236,0.18); }}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
    background: #141a22; color: #E6E8EC;
    border: 1px solid rgba(230,232,236,0.12);
    border-radius: 10px; padding: 8px 10px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid #6ea8fe; outline: none;
}}

/* Check con tilde (si hay recurso) */
QCheckBox {{ spacing: 8px; color: #E6E8EC; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 6px;
    background: #0f141c;
    border: 1px solid rgba(230,232,236,0.35);
}}
QCheckBox::indicator:hover {{ border-color: rgba(230,232,236,0.55); }}
QCheckBox::indicator:checked {{
    background: #0f141c;
    border: 1px solid #22c55e;
    {_CHECK_IMAGE_LINE}
}}

/* ===== Sidebar cálida ===== */
#Sidebar {{
    background: #E9E1D5;
    border-right: 1px solid rgba(0,0,0,0.06);
}}
#SideLogo {{ color: #2A2A2A; padding: 16px 14px 10px 14px; }}
.SideBtn {{
    text-align: left; padding: 10px 14px; border-radius: 10px; border: 1px solid transparent;
    color: #4A4A4A; background: transparent; font-weight: 700;
}}
.SideBtn:hover {{ background: #F4EEE6; border-color: rgba(0,0,0,0.05); }}
.SideBtn[active="true"] {{ background: #FFF9F0; color: #2A2A2A; border-color: rgba(0,0,0,0.08); }}

/* ===== Área cálida del dashboard ===== */
#WarmDash {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #F6F1EA, stop:1 #EFE7DB);
    padding: 16px; color: #2A2A2A;
}}
#WarmDash QLabel {{ color: #2A2A2A; }}

/* ===== KPI mate claros + texto blanco ===== */
#KpiOlive  {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8DA091, stop:1 #748B7D);
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 14px;
}}
#KpiAmber  {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #CBA866, stop:1 #B08C49);
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 14px;
}}
#KpiIndigo {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #879BB0, stop:1 #6E859A);
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 14px;
}}
#KpiRed    {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #C0837B, stop:1 #A16861);
    border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 14px;
}}
#KpiOlive QLabel, #KpiOlive QWidget,
#KpiAmber QLabel, #KpiAmber QWidget,
#KpiIndigo QLabel, #KpiIndigo QWidget,
#KpiRed   QLabel, #KpiRed   QWidget {{
    background: transparent;
    color: #FFFFFF;
}}
#KpiTitle {{ color:#FFFFFF; font-weight:800; letter-spacing:.2px; }}
#KpiValue {{ color:#FFFFFF; font-size:26px; font-weight:900; }}

/* ====== SECCIONES claras ====== */
#SectionCard {{
    background: #FFF9F0;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 12px;
}}
#SectionTitle {{
    font-weight: 900;
    color: #2A2A2A;
    border: none;
    padding: 0;
    margin: 0 0 8px 0;
}}

/* ====== Tabla de Últimos presupuestos ====== */
#UltimosPresTable QHeaderView::section {{
    background: #F2E9DB;
    color: #1C1E22;
    font-weight: 700;
    padding: 6px 8px;
    border: none;
}}
/* Texto negro y sin borde/selección azul */
QTableWidget#UltimosPresTable {{
    background: #FFF9F0; color:#1C1E22; border:none; border-radius:12px;
    selection-background-color: transparent;
    selection-color: #1C1E22;
}}
QTableWidget#UltimosPresTable::item {{
    color:#1C1E22;
}}
QTableView::item:selected,
QTableView::item:!active:selected,
QTableWidget::item:selected:active {{
    background: transparent;
    color: #1C1E22;
}}
QTableWidget#UltimosPresTable::focus {{ outline: none; }}

/* ===== Badges tipo píldora (uso de propiedad dinám. 'pill') ===== */
QLabel[pill="true"]{{
    border-radius: 999px;
    padding: 3px 10px;
    font-weight: 700;
    min-height: 24px;
    background: transparent;   /* nunca azul */
}}
#PillYellow {{ background: #F5E6A3; color:#1F2937; border:1px solid rgba(0,0,0,.08); }}
#PillGreen  {{ background: #BFE8C7; color:#10341F; border:1px solid rgba(0,0,0,.08); }}
#PillGray   {{ background: #C9CED6; color:#0F172A; border:1px solid rgba(0,0,0,.08); }}
"""

# ===== Helpers visuales (reusables) =====
def apply_card_shadow(widget, blur=24, dx=0, dy=12, color="#000000", alpha=110):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur); eff.setOffset(dx, dy)
    c = QColor(color); c.setAlpha(alpha); eff.setColor(c)
    widget.setGraphicsEffect(eff)

def add_hover_lift(widget, blur_in=28, blur_out=18, dy_in=6, dy_out=12, duration=140):
    eff = widget.graphicsEffect()
    if not isinstance(eff, QGraphicsDropShadowEffect):
        apply_card_shadow(widget, blur=blur_out, dy=dy_out); eff = widget.graphicsEffect()
    anim_in = QPropertyAnimation(eff, b"blurRadius", widget); anim_in.setDuration(duration); anim_in.setEasingCurve(QEasingCurve.OutCubic); anim_in.setStartValue(blur_out); anim_in.setEndValue(blur_in)
    anim_out = QPropertyAnimation(eff, b"blurRadius", widget); anim_out.setDuration(duration); anim_out.setEasingCurve(QEasingCurve.OutCubic); anim_out.setStartValue(blur_in); anim_out.setEndValue(blur_out)
    old_enter = getattr(widget, "enterEvent", None); old_leave = getattr(widget, "leaveEvent", None)
    def _enter(e):
        try: eff.setOffset(0, dy_in); anim_out.stop(); anim_in.start()
        except Exception: pass
        if callable(old_enter): old_enter(e)
    def _leave(e):
        try: eff.setOffset(0, dy_out); anim_in.stop(); anim_out.start()
        except Exception: pass
        if callable(old_leave): old_leave(e)
    widget.enterEvent = _enter; widget.leaveEvent = _leave