# app/ui/widgets.py
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath
from app.ui.category_data import get_initials
from app.ui.styles import PRODUCT_CARD_STYLE, CART_STYLE
from app.database import SessionLocal
from app.models import Product


def money(v):
    if v is None:
        v = 0
    if float(v) == int(v):
        return f"Rs. {int(v):,}"
    return f"Rs. {v:,.2f}"


# =========================================================
# CHART WIDGETS (Custom-painted, no external deps)
# =========================================================
class BarChartWidget(QWidget):
    """Simple bar chart for sales data"""
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or []  # list of (label, value)
        self.setMinimumHeight(220)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding_left = 60
        padding_right = 20
        padding_top = 20
        padding_bottom = 40

        chart_w = w - padding_left - padding_right
        chart_h = h - padding_top - padding_bottom

        # Background
        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))

        if not self.data:
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "No data available")
            return

        max_val = max(v for _, v in self.data) if self.data else 1
        if max_val == 0:
            max_val = 1

        # Draw Y-axis grid lines
        painter.setPen(QPen(QColor("#F1F5F9"), 1))
        for i in range(5):
            y = padding_top + (chart_h * i / 4)
            painter.drawLine(padding_left, int(y), w - padding_right, int(y))

            # Y labels
            val = max_val * (4 - i) / 4
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(5, int(y) + 4, 50, 20, Qt.AlignRight | Qt.AlignVCenter,
                             f"{int(val):,}")
            painter.setPen(QPen(QColor("#F1F5F9"), 1))

        # Draw bars
        n = len(self.data)
        if n == 0:
            return
        bar_slot = chart_w / n
        bar_w = bar_slot * 0.55

        for i, (label, value) in enumerate(self.data):
            bar_h = (value / max_val) * chart_h if max_val > 0 else 0
            x = padding_left + i * bar_slot + (bar_slot - bar_w) / 2
            y = padding_top + chart_h - bar_h

            # Bar gradient
            path = QPainterPath()
            radius = 6
            path.addRoundedRect(x, y, bar_w, bar_h, radius, radius)

            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor("#6366F1"))
            grad.setColorAt(1, QColor("#4F46E5"))
            painter.fillPath(path, QBrush(grad))

            # Value on top
            if value > 0:
                painter.setPen(QColor("#4F46E5"))
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.drawText(int(x - 10), int(y) - 20, int(bar_w + 20), 20,
                                 Qt.AlignCenter, f"{int(value):,}")

            # X-axis label
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(int(x - 10), h - padding_bottom + 8, int(bar_w + 20), 30,
                             Qt.AlignCenter, label)

        painter.end()


class DonutChartWidget(QWidget):
    """Donut chart for category breakdown"""
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or []  # list of (label, value)
        self.setMinimumHeight(220)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, QColor("#FFFFFF"))

        if not self.data:
            painter.setPen(QColor("#94A3B8"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(0, 0, w, h, Qt.AlignCenter, "No data available")
            return

        # Colors
        colors = [
            "#4F46E5", "#059669", "#D97706", "#DC2626",
            "#7C3AED", "#0891B2", "#DB2777", "#65A30D",
        ]

        total = sum(v for _, v in self.data)
        if total == 0:
            total = 1

        # Draw donut
        donut_size = min(w, h) - 60
        donut_x = 40
        donut_y = (h - donut_size) / 2
        rect = (donut_x, int(donut_y), donut_size, donut_size)

        start_angle = 90 * 16  # Start from top
        for i, (label, value) in enumerate(self.data):
            span = int((value / total) * 360 * 16)
            color = QColor(colors[i % len(colors)])
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawPie(*rect, start_angle, -span)
            start_angle -= span

        # Donut hole
        hole_size = int(donut_size * 0.55)
        hole_x = donut_x + (donut_size - hole_size) // 2
        hole_y = int(donut_y + (donut_size - hole_size) / 2)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(hole_x, hole_y, hole_size, hole_size)

        # Center text
        painter.setPen(QColor("#0F172A"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(hole_x, hole_y, hole_size, hole_size,
                         Qt.AlignCenter, f"{int(total):,}")

        # Legend
        legend_x = donut_x + donut_size + 20
        legend_y = 40
        painter.setFont(QFont("Segoe UI", 10))

        for i, (label, value) in enumerate(self.data):
            color = QColor(colors[i % len(colors)])

            # Color box
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(legend_x, legend_y, 12, 12, 3, 3)

            # Text
            painter.setPen(QColor("#0F172A"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(legend_x + 20, legend_y + 12, label[:15])

            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(legend_x + 20, legend_y + 26, f"{int(value):,} ({int(value/total*100)}%)")

            legend_y += 45
            if legend_y > h - 40:
                break

        painter.end()


from PySide6.QtGui import QLinearGradient


# =========================================================
# PRODUCT CARD
# =========================================================
class ProductCard(QFrame):
    clicked = Signal(int)

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setObjectName("ProductCard")
        self.setStyleSheet(PRODUCT_CARD_STYLE)
        self.setFixedSize(170, 175)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(4)

        avatar = QLabel(get_initials(product.name))
        avatar.setObjectName("InitialIcon")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(42, 42)
        avatar.setStyleSheet(PRODUCT_CARD_STYLE)
        top.addWidget(avatar)
        top.addStretch()

        if product.wholesale_price > 0 and product.wholesale_min_qty > 0:
            wbadge = QLabel(f"W{int(product.wholesale_min_qty)}+")
            wbadge.setStyleSheet("""
                background: #10B981; color: white;
                border-radius: 4px; padding: 2px 6px;
                font-size: 9px; font-weight: 800;
            """)
            top.addWidget(wbadge, 0, Qt.AlignTop)
        layout.addLayout(top)

        layout.addStretch()

        name = QLabel(product.name)
        name.setObjectName("ProductName")
        name.setStyleSheet(PRODUCT_CARD_STYLE)
        name.setWordWrap(True)
        name.setMaximumHeight(32)
        layout.addWidget(name)

        sku_text = product.sku or product.barcode or "—"
        sku = QLabel(f"SKU: {sku_text}")
        sku.setObjectName("ProductSku")
        sku.setStyleSheet(PRODUCT_CARD_STYLE)
        layout.addWidget(sku)

        price = QLabel(money(product.selling_price))
        price.setObjectName("ProductPrice")
        price.setStyleSheet(PRODUCT_CARD_STYLE)
        layout.addWidget(price)

        if product.wholesale_price > 0:
            wtext = QLabel(f"W: {money(product.wholesale_price)} ({int(product.wholesale_min_qty)}+)")
            wtext.setStyleSheet("color: #059669; font-size: 10px; font-weight: 700; background: transparent;")
            layout.addWidget(wtext)
        else:
            spacer = QLabel("")
            spacer.setFixedHeight(12)
            layout.addWidget(spacer)

        stock = product.stock_quantity
        if stock <= 0:
            s = QLabel("OUT OF STOCK")
            s.setObjectName("ProductStockOut")
        elif product.minimum_stock and stock <= product.minimum_stock:
            s = QLabel(f"{stock:.0f} LOW")
            s.setObjectName("ProductStockLow")
        else:
            s = QLabel(f"Stock: {stock:.0f}")
            s.setObjectName("ProductStock")
        s.setStyleSheet(PRODUCT_CARD_STYLE)
        layout.addWidget(s)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.product.id)


class CategoryButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("CatBtn")
        self.setCheckable(True)
        self.setFixedSize(66, 62)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 6, 2, 4)
        layout.setSpacing(2)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent; color: inherit;")

        text_lbl = QLabel(label)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setStyleSheet("font-size: 9px; background: transparent; color: inherit; font-weight: 700;")
        text_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)


class CartItemWidget(QFrame):
    qty_changed = Signal(int, float)
    removed = Signal(int)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("CartItemRow")
        self.setStyleSheet(CART_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        info = QVBoxLayout()
        info.setSpacing(3)

        name_row = QHBoxLayout()
        name_row.setSpacing(6)

        name = QLabel(item["name"])
        name.setObjectName("CartItemName")
        name.setStyleSheet(CART_STYLE)
        name_row.addWidget(name)

        if item.get("is_wholesale"):
            wbadge = QLabel("W")
            wbadge.setStyleSheet("""
                background: #10B981; color: white;
                border-radius: 3px; padding: 1px 5px;
                font-size: 9px; font-weight: 800;
            """)
            name_row.addWidget(wbadge)

        name_row.addStretch()
        info.addLayout(name_row)

        if item.get("is_wholesale"):
            meta = QLabel(f"{money(item['price'])} × {item['qty']:.0f}  (wholesale)")
        else:
            meta = QLabel(f"{money(item['price'])}  ×  {item['qty']:.0f}")
        meta.setObjectName("CartItemMeta")
        meta.setStyleSheet(CART_STYLE)
        info.addWidget(meta)

        layout.addLayout(info, 1)

        qty_box = QHBoxLayout()
        qty_box.setSpacing(3)

        minus = QPushButton("−")
        minus.setObjectName("QtyBtn")
        minus.setStyleSheet(CART_STYLE)
        minus.setCursor(Qt.PointingHandCursor)
        minus.clicked.connect(lambda: self.qty_changed.emit(item["id"], item["qty"] - 1))

        qty_lbl = QLabel(f"{item['qty']:.0f}")
        qty_lbl.setObjectName("QtyLabel")
        qty_lbl.setStyleSheet(CART_STYLE)
        qty_lbl.setAlignment(Qt.AlignCenter)

        plus = QPushButton("+")
        plus.setObjectName("QtyBtn")
        plus.setStyleSheet(CART_STYLE)
        plus.setCursor(Qt.PointingHandCursor)
        plus.clicked.connect(lambda: self.qty_changed.emit(item["id"], item["qty"] + 1))

        qty_box.addWidget(minus)
        qty_box.addWidget(qty_lbl)
        qty_box.addWidget(plus)
        layout.addLayout(qty_box)

        total = QLabel(money(item["price"] * item["qty"]))
        total.setObjectName("CartItemTotal")
        total.setStyleSheet(CART_STYLE)
        total.setFixedWidth(76)
        total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(total)

        rm = QPushButton("✕")
        rm.setObjectName("RemoveBtn")
        rm.setStyleSheet(CART_STYLE)
        rm.setCursor(Qt.PointingHandCursor)
        rm.clicked.connect(lambda: self.removed.emit(item["id"]))
        layout.addWidget(rm)


class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: str = "", color: str = "#4F46E5", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid #E8ECF1;
                border-radius: 14px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        if icon:
            icon_box = QLabel(icon)
            icon_box.setAlignment(Qt.AlignCenter)
            icon_box.setFixedSize(44, 44)
            icon_box.setStyleSheet(f"""
                background: {color}15;
                color: {color};
                border-radius: 10px;
                font-size: 20px;
                font-weight: 700;
            """)
            top.addWidget(icon_box)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("color: #8B95A5; font-size: 10px; font-weight: 800; letter-spacing: 1px; background: transparent;")
        title_box.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("color: #64748B; font-size: 11px; background: transparent;")
            title_box.addWidget(sub_lbl)

        top.addLayout(title_box)
        top.addStretch()
        layout.addLayout(top)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 900; background: transparent; letter-spacing: -0.5px;")
        layout.addWidget(val_lbl)

        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet(f"background: {color}; border-radius: 2px;")
        accent.setMaximumWidth(40)
        layout.addWidget(accent)


# =========================================================
# FIXED LIVE SEARCH BAR
# =========================================================
class LiveSearchBar(QLineEdit):
    """
    Fixed live search - types letter by letter, shows dropdown suggestions.
    The previous issue was the QTimer debounce + popup stealing focus.
    """
    product_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍  Search products by name, barcode or SKU...")
        self.setFixedHeight(44)

        # Dropdown
        self.dropdown = QListWidget()
        self.dropdown.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.dropdown.setFocusPolicy(Qt.NoFocus)  # Don't steal focus from search bar
        self.dropdown.setStyleSheet("""
            QListWidget {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                color: #0F172A;
            }
            QListWidget::item:hover { background: #EEF2FF; }
            QListWidget::item:selected { background: #4F46E5; color: white; }
        """)
        self.dropdown.itemClicked.connect(self._on_item_clicked)

        # Debounce timer - 200ms to keep typing responsive
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._do_search)

        # CRITICAL FIX: use textEdited (fires on every keystroke) not textChanged
        self.textEdited.connect(self._on_text_edited)
        self.returnPressed.connect(self._on_enter)

    def _on_text_edited(self, text):
        """Called on every keystroke - debounced search"""
        if not text.strip():
            self.dropdown.hide()
            return
        # Restart timer on every keystroke (debouncing)
        self.timer.stop()
        self.timer.start()

    def _do_search(self):
        q = self.text().strip()
        if not q:
            self.dropdown.hide()
            return

        with SessionLocal() as s:
            products = s.query(Product).filter(
                Product.active == True,
                (Product.name.ilike(f"%{q}%")) |
                (Product.barcode.ilike(f"%{q}%")) |
                (Product.sku.ilike(f"%{q}%"))
            ).limit(10).all()

            self.dropdown.clear()
            if not products:
                item = QListWidgetItem("No products found")
                item.setFlags(Qt.NoItemFlags)
                self.dropdown.addItem(item)
            else:
                for p in products:
                    text = f"{p.name}   •   {p.sku or p.barcode}   •   Rs. {p.selling_price:.0f}   •   Stock: {p.stock_quantity:.0f}"
                    item = QListWidgetItem(text)
                    item.setData(Qt.UserRole, p.id)
                    self.dropdown.addItem(item)

        # Show dropdown positioned below search bar
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        self.dropdown.setFixedWidth(self.width())
        self.dropdown.move(global_pos.x(), global_pos.y() + 4)
        row_h = 42
        h = min(380, row_h * self.dropdown.count() + 12)
        self.dropdown.setFixedHeight(max(60, h))
        self.dropdown.show()
        self.dropdown.raise_()
        # DON'T steal focus back - user should keep typing

    def _on_item_clicked(self, item):
        pid = item.data(Qt.UserRole)
        if pid:
            self.product_selected.emit(pid)
            self.clear()
            self.dropdown.hide()

    def _on_enter(self):
        """Enter key - select first item"""
        if self.dropdown.count() > 0:
            item = self.dropdown.item(0)
            pid = item.data(Qt.UserRole)
            if pid:
                self.product_selected.emit(pid)
                self.clear()
                self.dropdown.hide()

    def keyPressEvent(self, event):
        # Arrow navigation while typing
        if self.dropdown.isVisible():
            if event.key() == Qt.Key_Down:
                self.dropdown.setCurrentRow(
                    min(self.dropdown.currentRow() + 1, self.dropdown.count() - 1)
                )
                return
            if event.key() == Qt.Key_Up:
                self.dropdown.setCurrentRow(
                    max(self.dropdown.currentRow() - 1, 0)
                )
                return
            if event.key() == Qt.Key_Escape:
                self.dropdown.hide()
                return
        super().keyPressEvent(event)