# app/ui/styles.py
"""Premium POS Design System + Credit System Styles"""

COLORS = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_light": "#EEF2FF",
    "bg": "#F1F5F9",
    "surface": "#FFFFFF",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_light": "#94A3B8",
    "border": "#E2E8F0",
    "success": "#059669",
    "danger": "#DC2626",
    "warning": "#D97706",
    "sidebar": "#0F172A",
}


GLOBAL_STYLE = """
* {
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    outline: none;
}
QMainWindow, QWidget {
    background: #F1F5F9;
    color: #0F172A;
    font-size: 13px;
}
QToolTip {
    background: #0F172A; color: white;
    padding: 6px 10px; border-radius: 4px; font-size: 12px;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: #0F172A;
    selection-background-color: #4F46E5;
    selection-color: white;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #4F46E5;
    padding: 9px 13px;
}
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #64748B;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #EEF2FF;
    selection-color: #4F46E5;
    outline: none;
}
QPushButton {
    background: #4F46E5; color: #FFFFFF;
    border: none; border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px; font-weight: 600;
    min-height: 18px;
}
QPushButton:hover { background: #4338CA; }
QPushButton:pressed { background: #3730A3; }
QPushButton:disabled { background: #E2E8F0; color: #94A3B8; }
QPushButton[variant="secondary"] {
    background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;
}
QPushButton[variant="secondary"]:hover { background: #F8FAFC; border-color: #94A3B8; }
QPushButton[variant="success"] { background: #059669; color: white; }
QPushButton[variant="success"]:hover { background: #047857; }
QPushButton[variant="danger"] { background: #DC2626; }
QPushButton[variant="danger"]:hover { background: #B91C1C; }
QPushButton[variant="ghost"] {
    background: transparent; color: #64748B; border: none; padding: 8px 12px;
}
QPushButton[variant="ghost"]:hover { background: #F1F5F9; color: #0F172A; }
QTableWidget {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #EEF2FF;
    selection-color: #0F172A;
    outline: none;
}
QTableWidget::item {
    padding: 10px 8px;
    border-bottom: 1px solid #F1F5F9;
}
QTableWidget::item:selected { background: #EEF2FF; color: #0F172A; }
QHeaderView::section {
    background: #F8FAFC;
    padding: 12px 10px;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 700;
    color: #64748B;
    font-size: 11px;
    letter-spacing: 0.5px;
}
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 5px; min-height: 40px; }
QScrollBar::handle:vertical:hover { background: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #CBD5E1; border-radius: 5px; min-width: 40px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QGroupBox {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    margin-top: 14px;
    padding: 20px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #64748B;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QDialog { background: #FFFFFF; }
QLabel { background: transparent; }
QTextEdit {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}
"""


SIDEBAR_STYLE = """
QFrame#Sidebar { background: #0F172A; border: none; }
QLabel#BrandLogo {
    color: #FFFFFF; font-size: 20px; font-weight: 800;
    letter-spacing: 1px; padding: 4px;
}
QLabel#BrandTag {
    color: #64748B; font-size: 10px; font-weight: 600; letter-spacing: 2px;
}
QFrame#UserCard { background: #1E293B; border-radius: 10px; }
QLabel#UserAvatar {
    background: #4F46E5; color: white; border-radius: 18px;
    font-size: 15px; font-weight: 700;
}
QLabel#UserName { color: #F1F5F9; font-size: 13px; font-weight: 700; }
QLabel#UserRole { color: #64748B; font-size: 11px; }
QLabel#SectionLabel {
    color: #475569; font-size: 10px; font-weight: 700;
    letter-spacing: 1.5px; padding: 6px 8px 2px 8px;
}
QPushButton#NavButton {
    background: transparent; color: #CBD5E1;
    text-align: left; padding: 11px 14px;
    border-radius: 8px; font-weight: 500;
    font-size: 13px; border: none;
}
QPushButton#NavButton:hover { background: #1E293B; color: #FFFFFF; }
QPushButton#NavButton:checked { background: #4F46E5; color: #FFFFFF; font-weight: 600; }
"""


TOPBAR_STYLE = """
QFrame#TopBar { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }
QLineEdit#SearchBar {
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 11px 16px;
    font-size: 13px; color: #0F172A;
}
QLineEdit#SearchBar:focus {
    background: #FFFFFF; border: 2px solid #4F46E5;
    padding: 10px 15px;
}
QPushButton#IconBtn {
    background: transparent; border: none; border-radius: 8px;
    padding: 8px; min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px;
    color: #64748B; font-size: 16px;
}
QPushButton#IconBtn:hover { background: #F1F5F9; color: #4F46E5; }
"""


CATEGORY_STYLE = """
QFrame#CategoryBar { background: #FFFFFF; border-right: 1px solid #E2E8F0; }
QPushButton#CatBtn {
    background: transparent; color: #64748B;
    border: none; border-radius: 8px;
    padding: 8px 2px; font-size: 10px; font-weight: 600; text-align: center;
}
QPushButton#CatBtn:hover { background: #F8FAFC; color: #0F172A; }
QPushButton#CatBtn:checked { background: #EEF2FF; color: #4F46E5; }
"""


PRODUCT_CARD_STYLE = """
QFrame#ProductCard {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
}
QFrame#ProductCard:hover { border: 2px solid #4F46E5; background: #FFFFFF; }
QLabel#ProductName {
    color: #0F172A; font-size: 12px; font-weight: 600; background: transparent;
}
QLabel#ProductSku {
    color: #94A3B8; font-size: 10px; background: transparent;
}
QLabel#ProductPrice {
    color: #0F172A; font-size: 15px; font-weight: 800; background: transparent;
}
QLabel#ProductStock {
    color: #64748B; font-size: 10px; font-weight: 600; background: transparent;
}
QLabel#ProductStockLow {
    color: #D97706; font-size: 10px; font-weight: 700; background: transparent;
}
QLabel#ProductStockOut {
    color: #DC2626; font-size: 10px; font-weight: 700; background: transparent;
}
QLabel#DiscountBadge {
    background: #DC2626; color: #FFFFFF; border-radius: 4px;
    padding: 2px 6px; font-size: 9px; font-weight: 800;
}
QLabel#InitialIcon {
    background: #EEF2FF; color: #4F46E5; border-radius: 8px;
    font-size: 22px; font-weight: 800;
}
"""


CART_STYLE = """
QFrame#CartPanel { background: #FFFFFF; border-left: 1px solid #E2E8F0; }
QFrame#CartHeader { background: #FFFFFF; border-bottom: 1px solid #E2E8F0; }
QLabel#CartTitle { color: #0F172A; font-size: 15px; font-weight: 800; }
QLabel#CartSubtitle { color: #94A3B8; font-size: 11px; }
QFrame#CartItemRow { background: #FFFFFF; border-bottom: 1px solid #F1F5F9; }
QLabel#CartItemName { color: #0F172A; font-size: 12px; font-weight: 700; }
QLabel#CartItemMeta { color: #64748B; font-size: 11px; }
QLabel#CartItemTotal { color: #0F172A; font-size: 13px; font-weight: 800; }
QPushButton#QtyBtn {
    background: #F1F5F9; color: #0F172A; border-radius: 6px;
    min-width: 26px; max-width: 26px; min-height: 26px; max-height: 26px;
    padding: 0; font-weight: 800; font-size: 14px; border: none;
}
QPushButton#QtyBtn:hover { background: #4F46E5; color: white; }
QLabel#QtyLabel {
    color: #0F172A; font-size: 13px; font-weight: 800; min-width: 28px;
}
QPushButton#RemoveBtn {
    background: transparent; color: #94A3B8; border: none;
    padding: 2px; min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px; font-size: 14px; font-weight: 700;
}
QPushButton#RemoveBtn:hover {
    color: #DC2626; background: #FEF2F2; border-radius: 6px;
}
QFrame#CartFooter { background: #FFFFFF; border-top: 1px solid #E2E8F0; }
QLabel#TotalLabel {
    color: #64748B; font-size: 11px; font-weight: 800; letter-spacing: 1px;
}
QLabel#TotalValue { color: #0F172A; font-size: 26px; font-weight: 900; }
QLabel#SubLabel { color: #64748B; font-size: 12px; }
QLabel#SubValue { color: #0F172A; font-size: 13px; font-weight: 700; }
QPushButton#CheckoutBtn {
    background: #059669; color: #FFFFFF; border-radius: 10px;
    padding: 14px; font-size: 14px; font-weight: 800; letter-spacing: 0.5px;
}
QPushButton#CheckoutBtn:hover { background: #047857; }
QPushButton#CheckoutBtn:disabled { background: #E2E8F0; color: #94A3B8; }
"""


LOGIN_STYLE = """
QDialog { background: #FFFFFF; }
QLabel#LoginBrand {
    color: #4F46E5; font-size: 26px; font-weight: 900; letter-spacing: 1px;
}
QLabel#LoginTitle { color: #0F172A; font-size: 20px; font-weight: 800; }
QLabel#LoginSub { color: #64748B; font-size: 13px; }
QLabel#FieldLabel { color: #334155; font-size: 12px; font-weight: 700; }
QLineEdit#LoginInput {
    background: #FFFFFF; border: 2px solid #CBD5E1;
    border-radius: 10px; padding: 14px 16px;
    font-size: 14px; color: #0F172A; font-weight: 500;
}
QLineEdit#LoginInput:focus { border: 2px solid #4F46E5; background: #FFFFFF; }
QPushButton#LoginBtn {
    background: #4F46E5; color: #FFFFFF; border-radius: 10px;
    padding: 14px; font-size: 14px; font-weight: 800;
}
QPushButton#LoginBtn:hover { background: #4338CA; }
QLabel#LoginError { color: #DC2626; font-size: 12px; font-weight: 600; }
QLabel#LoginHint { color: #94A3B8; font-size: 11px; }
QFrame#LoginDivider { background: #E2E8F0; max-height: 1px; min-height: 1px; }
"""


DIALOG_STYLE = """
QDialog { background: #FFFFFF; }
QLabel#DialogTitle { color: #0F172A; font-size: 18px; font-weight: 800; }
QLabel#DialogSub { color: #64748B; font-size: 12px; }
QFrame#SummaryBox { background: #EEF2FF; border-radius: 10px; }
QLabel#SummaryLabel {
    color: #4F46E5; font-size: 11px; font-weight: 800; letter-spacing: 1px;
}
QLabel#SummaryValue { color: #4F46E5; font-size: 24px; font-weight: 900; }
QLabel#FieldLabelDark { color: #334155; font-size: 12px; font-weight: 700; }
"""


CREDIT_DIALOG_STYLE = """
QDialog { background: #FFFFFF; }
QLabel#CreditTitle { color: #0F172A; font-size: 20px; font-weight: 800; }
QLabel#CreditSub { color: #64748B; font-size: 12px; }
QLabel#CreditLabel { color: #334155; font-size: 12px; font-weight: 700; }
QFrame#CreditSummary { background: #FEF3C7; border-radius: 10px; }
QLabel#CreditSummaryLabel {
    color: #92400E; font-size: 11px; font-weight: 800; letter-spacing: 1px;
}
QLabel#CreditSummaryValue { color: #92400E; font-size: 22px; font-weight: 900; }
QFrame#GreenSummary { background: #ECFDF5; border-radius: 10px; }
QLabel#GreenLabel {
    color: #047857; font-size: 11px; font-weight: 800; letter-spacing: 1px;
}
QLabel#GreenValue { color: #047857; font-size: 22px; font-weight: 900; }
"""


CREDITS_PAGE_STYLE = """
QFrame#CreditStatCard {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
}
QLabel#StatLabel {
    color: #64748B; font-size: 11px; font-weight: 800; letter-spacing: 0.8px;
}
QLabel#StatValueBig { color: #0F172A; font-size: 26px; font-weight: 900; }
"""