# app/ui/main_window.py
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QLinearGradient
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from app.database import SessionLocal
from app.models import (
    User, Product, Category, Sale, SaleItem, HeldSale,
    HeldSaleItem, Customer, InventoryMovement, Setting,
    CreditCustomer, CreditTransaction
)
import bcrypt, shutil, csv
from datetime import datetime, date, timedelta
from collections import defaultdict

from app.ui.styles import (
    GLOBAL_STYLE, SIDEBAR_STYLE, TOPBAR_STYLE, CATEGORY_STYLE,
    CART_STYLE, LOGIN_STYLE, DIALOG_STYLE, CREDIT_DIALOG_STYLE,
    CREDITS_PAGE_STYLE
)
from app.ui.category_data import CATEGORY_ICONS
from app.ui.widgets import (
    ProductCard, CategoryButton, CartItemWidget, StatCard,
    LiveSearchBar, money, BarChartWidget, DonutChartWidget
)


# =========================================================
# PERMISSIONS SYSTEM
# =========================================================
ROLE_PERMISSIONS = {
    "Admin": {
        "dashboard": True, "pos": True, "products": True,
        "inventory": True, "sales": True, "credits": True,
        "users": True, "backup": True,
    },
    "Manager": {
        "dashboard": True, "pos": True, "products": True,
        "inventory": True, "sales": True, "credits": True,
        "users": False, "backup": True,
    },
    "Cashier": {
        "dashboard": False, "pos": True, "products": False,
        "inventory": False, "sales": False, "credits": True,
        "users": False, "backup": False,
    },
}


def has_permission(role, key):
    return ROLE_PERMISSIONS.get(role, {}).get(key, False)


# =========================================================
# LOGIN DIALOG
# =========================================================
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user = None
        self.setWindowTitle("Retail POS — Sign In")
        self.setFixedSize(440, 560)
        self.setStyleSheet(LOGIN_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 40)
        layout.setSpacing(6)

        brand = QLabel("RETAIL POS")
        brand.setObjectName("LoginBrand")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(brand)

        layout.addSpacing(28)

        title = QLabel("Welcome back")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(title)

        sub = QLabel("Sign in to continue to your account")
        sub.setObjectName("LoginSub")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(sub)

        layout.addSpacing(28)

        u_lbl = QLabel("USERNAME")
        u_lbl.setObjectName("FieldLabel")
        u_lbl.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(u_lbl)

        self.u = QLineEdit()
        self.u.setObjectName("LoginInput")
        self.u.setPlaceholderText("Enter your username")
        self.u.setStyleSheet(LOGIN_STYLE)
        self.u.setFixedHeight(50)
        layout.addWidget(self.u)

        layout.addSpacing(12)

        p_lbl = QLabel("PASSWORD")
        p_lbl.setObjectName("FieldLabel")
        p_lbl.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(p_lbl)

        self.p = QLineEdit()
        self.p.setObjectName("LoginInput")
        self.p.setPlaceholderText("Enter your password")
        self.p.setEchoMode(QLineEdit.Password)
        self.p.setStyleSheet(LOGIN_STYLE)
        self.p.setFixedHeight(50)
        self.p.returnPressed.connect(self.login)
        layout.addWidget(self.p)

        layout.addSpacing(8)

        self.msg = QLabel("")
        self.msg.setObjectName("LoginError")
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setStyleSheet(LOGIN_STYLE)
        self.msg.setMinimumHeight(18)
        layout.addWidget(self.msg)

        layout.addSpacing(8)

        btn = QPushButton("Sign In")
        btn.setObjectName("LoginBtn")
        btn.setStyleSheet(LOGIN_STYLE)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.login)
        layout.addWidget(btn)

        layout.addStretch()

        divider = QFrame()
        divider.setObjectName("LoginDivider")
        divider.setStyleSheet(LOGIN_STYLE)
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        layout.addSpacing(10)

        hint = QLabel("Default:  admin  /  admin123")
        hint.setObjectName("LoginHint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(LOGIN_STYLE)
        layout.addWidget(hint)

        QTimer.singleShot(100, self.u.setFocus)

    def login(self):
        with SessionLocal() as s:
            u = s.query(User).filter_by(username=self.u.text().strip(), active=True).first()
            if u and bcrypt.checkpw(self.p.text().encode(), u.password_hash.encode()):
                self.user = (u.id, u.username, u.role)
                self.accept()
            else:
                self.msg.setText("Invalid username or password")


# =========================================================
# USER DIALOG
# =========================================================
class UserDialog(QDialog):
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.result = None
        self.setWindowTitle("Add User" if not user_id else "Edit User")
        self.setFixedSize(480, 640)
        self.setStyleSheet(DIALOG_STYLE)

        data = None
        if user_id:
            with SessionLocal() as s:
                u = s.get(User, user_id)
                if u:
                    data = {
                        "username": u.username,
                        "full_name": u.full_name or u.username,
                        "role": u.role,
                        "active": u.active,
                    }

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Header
        h = QFrame()
        h.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        hl = QVBoxLayout(h)
        hl.setContentsMargins(28, 22, 28, 16)
        t = QLabel("Add User" if not user_id else "Edit User")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        hl.addWidget(t)
        s_lbl = QLabel("Create a new system user" if not user_id else "Update user details")
        s_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
        hl.addWidget(s_lbl)
        main.addWidget(h)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        body = QWidget()
        body.setStyleSheet("background: #FFFFFF;")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(28, 20, 28, 20)
        bv.setSpacing(12)

        def add_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
            bv.addWidget(lbl)

        def add_input(placeholder="", text="", echo=None):
            w = QLineEdit()
            w.setPlaceholderText(placeholder)
            w.setText(text)
            if echo:
                w.setEchoMode(echo)
            w.setFixedHeight(44)
            w.setStyleSheet("""
                QLineEdit {
                    background: #FFFFFF; border: 2px solid #CBD5E1;
                    border-radius: 10px; padding: 10px 14px;
                    font-size: 13px; color: #0F172A;
                }
                QLineEdit:focus { border: 2px solid #4F46E5; }
            """)
            bv.addWidget(w)
            return w

        add_label("Full Name *")
        self.full_name = add_input("e.g., Ali Ahmed", data["full_name"] if data else "")

        add_label("Username *")
        self.username = add_input("e.g., ali01", data["username"] if data else "")

        add_label("Password *" if not user_id else "New Password (leave blank to keep)")
        self.password = add_input("••••••••", "", QLineEdit.Password)

        add_label("Role *")
        self.role = QComboBox()
        self.role.addItems(["Cashier", "Manager", "Admin"])
        if data:
            idx = self.role.findText(data["role"])
            if idx >= 0:
                self.role.setCurrentIndex(idx)
        self.role.setFixedHeight(44)
        self.role.setStyleSheet("""
            QComboBox {
                background: #FFFFFF; border: 2px solid #CBD5E1;
                border-radius: 10px; padding: 10px 14px;
                font-size: 13px; color: #0F172A;
                font-weight: 600;
            }
            QComboBox:focus { border: 2px solid #4F46E5; }
            QComboBox::drop-down { border: none; width: 36px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #4F46E5;
                margin-right: 12px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                border: 2px solid #4F46E5;
                border-radius: 10px;
                padding: 6px;
                outline: none;
                selection-background-color: #EEF2FF;
                selection-color: #4F46E5;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #EEF2FF;
            }
        """)
        bv.addWidget(self.role)

        # Role description
        self.role_desc = QLabel()
        self.role_desc.setStyleSheet("""
            color: #64748B; font-size: 11px;
            background: #F8FAFC;
            padding: 10px 14px;
            border-radius: 8px;
        """)
        self.role_desc.setWordWrap(True)
        self._update_role_desc()
        self.role.currentIndexChanged.connect(self._update_role_desc)
        bv.addWidget(self.role_desc)

        # Active checkbox
        self.active_cb = QCheckBox("Active (can login to system)")
        self.active_cb.setChecked(data["active"] if data else True)
        self.active_cb.setStyleSheet("""
            QCheckBox {
                color: #334155; font-size: 13px; font-weight: 600;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border: 2px solid #CBD5E1;
                border-radius: 5px;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: #4F46E5;
                border: 2px solid #4F46E5;
            }
        """)
        bv.addWidget(self.active_cb)

        bv.addStretch()
        scroll.setWidget(body)
        main.addWidget(scroll, 1)

        # Footer
        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(28, 16, 28, 20)
        fl.setSpacing(12)

        cancel = QPushButton("Cancel")
        cancel.setProperty("variant", "secondary")
        cancel.setFixedHeight(48)
        cancel.setFixedWidth(120)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        fl.addWidget(cancel)

        save = QPushButton("💾  Save User")
        save.setFixedHeight(48)
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        fl.addWidget(save, 1)

        main.addWidget(footer)

    def _update_role_desc(self):
        role = self.role.currentText()
        descs = {
            "Admin": "Full access: Dashboard, POS, Products, Inventory, Sales, Credits, and User Management.",
            "Manager": "Access: Dashboard, POS, Products, Inventory, Sales, and Credits. No user management.",
            "Cashier": "Limited: POS and Udhaar/Credits only. No dashboard, products, inventory, or sales history.",
        }
        self.role_desc.setText(f"ℹ️  {descs.get(role, '')}")

    def _save(self):
        full_name = self.full_name.text().strip()
        username = self.username.text().strip()
        password = self.password.text()
        role = self.role.currentText()
        active = self.active_cb.isChecked()

        if not full_name:
            QMessageBox.warning(self, "Missing Info", "Full name is required.")
            return
        if not username:
            QMessageBox.warning(self, "Missing Info", "Username is required.")
            return
        if not self.user_id and not password:
            QMessageBox.warning(self, "Missing Info", "Password is required for new users.")
            return
        if password and len(password) < 4:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 4 characters.")
            return

        try:
            with SessionLocal() as s:
                existing = s.query(User).filter_by(username=username).first()
                if existing and existing.id != self.user_id:
                    QMessageBox.warning(self, "Duplicate", "Username already exists.")
                    return

                if self.user_id:
                    u = s.get(User, self.user_id)
                    if not u:
                        QMessageBox.warning(self, "Not Found", "User not found.")
                        return
                    u.full_name = full_name
                    u.username = username
                    u.role = role
                    u.active = active
                    if password:
                        u.password_hash = bcrypt.hashpw(
                            password.encode(), bcrypt.gensalt()
                        ).decode()
                else:
                    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    s.add(User(
                        username=username,
                        full_name=full_name,
                        password_hash=pw_hash,
                        role=role,
                        active=active,
                    ))
                s.commit()

            self.result = True
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", str(e))


# =========================================================
# USERS WIDGET (Admin only)
# =========================================================
class UsersWidget(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("User Management")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
        header.addWidget(title)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 600; padding-left: 12px;")
        header.addWidget(self.count_lbl)
        header.addStretch()

        add = QPushButton("+ Add User")
        add.setFixedHeight(40)
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add_user)
        header.addWidget(add)

        refresh = QPushButton("Refresh")
        refresh.setProperty("variant", "secondary")
        refresh.setFixedHeight(40)
        refresh.clicked.connect(self.load)
        header.addWidget(refresh)

        root.addLayout(header)

        # Info banner
        info = QFrame()
        info.setStyleSheet("background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px;")
        il = QHBoxLayout(info)
        il.setContentsMargins(16, 12, 16, 12)
        icon_lbl = QLabel("ℹ️")
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        il.addWidget(icon_lbl)
        text = QLabel(
            "<b>Roles:</b> "
            "<b>Admin</b> → full access  •  "
            "<b>Manager</b> → products, inventory, sales, credits  •  "
            "<b>Cashier</b> → POS and Udhaar only"
        )
        text.setStyleSheet("color: #4F46E5; font-size: 12px; background: transparent;")
        text.setWordWrap(True)
        il.addWidget(text, 1)
        root.addWidget(info)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["AVATAR", "NAME", "USERNAME", "ROLE", "STATUS", "ACTIONS"]
        )
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 180)

        root.addWidget(self.table, 1)
        self.load()

    def load(self):
        with SessionLocal() as s:
            users = s.query(User).order_by(User.role, User.username).all()
            data = [(u.id, u.username, u.full_name or u.username, u.role, u.active) for u in users]

        self.table.setRowCount(0)
        for uid, username, full_name, role, active in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 64)

            # Avatar
            av_widget = QWidget()
            av_l = QHBoxLayout(av_widget)
            av_l.setContentsMargins(0, 0, 0, 0)
            av_l.setAlignment(Qt.AlignCenter)
            av = QLabel((full_name or username)[0].upper())
            av.setAlignment(Qt.AlignCenter)
            av.setFixedSize(44, 44)
            av.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                color: white; border-radius: 22px;
                font-size: 18px; font-weight: 800;
            """)
            av_l.addWidget(av)
            self.table.setCellWidget(r, 0, av_widget)

            # Name
            name_item = QTableWidgetItem(full_name)
            fnt = name_item.font(); fnt.setBold(True); fnt.setPointSize(11)
            name_item.setFont(fnt)
            self.table.setItem(r, 1, name_item)

            # Username
            un_item = QTableWidgetItem(f"@{username}")
            un_item.setForeground(QColor("#64748B"))
            self.table.setItem(r, 2, un_item)

            # Role badge
            role_widget = QWidget()
            rl = QHBoxLayout(role_widget)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setAlignment(Qt.AlignCenter)
            rb = QLabel(role.upper())
            if role == "Admin":
                rb.setStyleSheet("""
                    background: #EEF2FF; color: #4F46E5;
                    border-radius: 6px; padding: 6px 14px;
                    font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
                """)
            elif role == "Manager":
                rb.setStyleSheet("""
                    background: #FEF3C7; color: #D97706;
                    border-radius: 6px; padding: 6px 14px;
                    font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
                """)
            else:
                rb.setStyleSheet("""
                    background: #ECFDF5; color: #059669;
                    border-radius: 6px; padding: 6px 14px;
                    font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
                """)
            rl.addWidget(rb)
            self.table.setCellWidget(r, 3, role_widget)

            # Status
            status_widget = QWidget()
            sl = QHBoxLayout(status_widget)
            sl.setContentsMargins(0, 0, 0, 0)
            sl.setAlignment(Qt.AlignCenter)
            sb = QLabel("● ACTIVE" if active else "● INACTIVE")
            sb.setStyleSheet(f"""
                color: {'#059669' if active else '#94A3B8'};
                font-size: 11px; font-weight: 800; letter-spacing: 0.5px;
            """)
            sl.addWidget(sb)
            self.table.setCellWidget(r, 4, status_widget)

            # Actions
            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 4, 4, 4)
            al.setSpacing(8)
            al.setAlignment(Qt.AlignCenter)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(34); edit_btn.setFixedWidth(70)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #EEF2FF; color: #4F46E5;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 700;
                }
                QPushButton:hover { background: #4F46E5; color: white; }
            """)
            edit_btn.clicked.connect(lambda _, uid=uid: self.edit_user(uid))
            al.addWidget(edit_btn)

            del_btn = QPushButton("Delete")
            del_btn.setFixedHeight(34); del_btn.setFixedWidth(80)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #FEF2F2; color: #DC2626;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 700;
                }
                QPushButton:hover { background: #DC2626; color: white; }
            """)
            del_btn.clicked.connect(lambda _, uid=uid, un=username: self.delete_user(uid, un))
            al.addWidget(del_btn)

            self.table.setCellWidget(r, 5, actions)

        self.count_lbl.setText(f"{len(data)} users")

    def add_user(self):
        dlg = UserDialog(user_id=None, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load()
            QMessageBox.information(self, "Success", "User created successfully.")

    def edit_user(self, uid):
        dlg = UserDialog(user_id=uid, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.load()
            QMessageBox.information(self, "Success", "User updated successfully.")

    def delete_user(self, uid, username):
        if username == "admin":
            QMessageBox.warning(self, "Not Allowed", "Cannot delete the primary admin account.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Delete User")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"<b>Delete user '@{username}'?</b>")
        msg.setInformativeText(
            "This action cannot be undone.\n"
            "All sales made by this user will remain in the database."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        if msg.exec() != QMessageBox.Yes:
            return

        try:
            with SessionLocal() as s:
                u = s.get(User, uid)
                if u:
                    s.delete(u)
                    s.commit()
            self.load()
            QMessageBox.information(self, "Deleted", f"User '{username}' deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", str(e))


# =========================================================
# HELD SALES DIALOG
# =========================================================
class HeldSalesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected = None
        self.setWindowTitle("Held Sales")
        self.setFixedSize(560, 500)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Held Sales")
        title.setObjectName("DialogTitle")
        title.setStyleSheet(DIALOG_STYLE)
        layout.addWidget(title)

        sub = QLabel("Select a held sale to resume or delete")
        sub.setObjectName("DialogSub")
        sub.setStyleSheet(DIALOG_STYLE)
        layout.addWidget(sub)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["REFERENCE", "DATE", "ITEMS", "TOTAL"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemDoubleClicked.connect(lambda _: self.resume())
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        del_btn = QPushButton("Delete")
        del_btn.setProperty("variant", "danger")
        del_btn.setFixedHeight(44)
        del_btn.clicked.connect(self.delete_selected)
        btn_row.addWidget(del_btn)

        btn_row.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setProperty("variant", "secondary")
        cancel.setFixedHeight(44)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        resume = QPushButton("Resume Sale")
        resume.setFixedHeight(44)
        resume.clicked.connect(self.resume)
        btn_row.addWidget(resume)

        layout.addLayout(btn_row)
        self.load()

    def load(self):
        with SessionLocal() as s:
            held = s.query(HeldSale).order_by(HeldSale.created_at.desc()).all()
            rows = []
            for h in held:
                items = s.query(HeldSaleItem).filter_by(held_sale_id=h.id).all()
                total = sum(i.subtotal for i in items)
                rows.append((h.id, h.reference, h.created_at, len(items), total))

        self.table.setRowCount(0)
        for hid, ref, dt, count, total in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 52)
            vals = [ref, dt.strftime("%d-%m-%Y %H:%M"), f"{count} items", money(total)]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.UserRole, hid)
                self.table.setItem(r, c, item)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def resume(self):
        hid = self.get_selected_id()
        if hid is None:
            QMessageBox.information(self, "No Selection", "Please select a held sale first.")
            return
        self.selected = hid
        self.accept()

    def delete_selected(self):
        hid = self.get_selected_id()
        if hid is None:
            QMessageBox.information(self, "No Selection", "Please select a held sale first.")
            return
        if QMessageBox.question(self, "Delete Held Sale", "Delete this held sale permanently?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        with SessionLocal() as s:
            h = s.get(HeldSale, hid)
            if h:
                s.delete(h)
                s.commit()
        self.load()


# =========================================================
# CHECKOUT DIALOG
# =========================================================
class CheckoutDialog(QDialog):
    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.total = total
        self.result_data = None

        self.setWindowTitle("Checkout")
        self.setFixedSize(520, 680)
        self.setStyleSheet(DIALOG_STYLE)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 22, 28, 16)
        hl.setSpacing(4)

        t = QLabel("Complete Payment")
        t.setObjectName("DialogTitle")
        t.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(t)

        s = QLabel("Choose payment type and fill details")
        s.setObjectName("DialogSub")
        s.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(s)
        main.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: #FFFFFF; border: none; }
            QScrollBar:vertical {
                background: #F1F5F9; width: 10px; border-radius: 5px;
                margin: 4px 2px 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1; border-radius: 5px; min-height: 40px;
            }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        body = QWidget()
        body.setStyleSheet("background: #FFFFFF;")
        v = QVBoxLayout(body)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(16)

        total_box = QFrame()
        total_box.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EEF2FF, stop:1 #E0E7FF);
                border-radius: 12px;
                border: 1px solid #C7D2FE;
            }
        """)
        tbl = QVBoxLayout(total_box)
        tbl.setContentsMargins(20, 16, 20, 16)
        tbl.setSpacing(4)

        lbl = QLabel("TOTAL AMOUNT")
        lbl.setStyleSheet("color: #4F46E5; font-size: 11px; font-weight: 800; letter-spacing: 1.2px; background: transparent;")
        tbl.addWidget(lbl)

        amt = QLabel(money(total))
        amt.setStyleSheet("color: #4F46E5; font-size: 28px; font-weight: 900; background: transparent;")
        tbl.addWidget(amt)
        v.addWidget(total_box)

        pl = QLabel("PAYMENT TYPE")
        pl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
        v.addWidget(pl)

        self.pay_type = QComboBox()
        self.pay_type.addItems(["💵  Full Payment", "📝  Partial Payment (Udhaar)"])
        self.pay_type.setFixedHeight(50)
        self.pay_type.setStyleSheet(self._combo_style())
        self.pay_type.currentIndexChanged.connect(self._on_type_changed)
        v.addWidget(self.pay_type)

        ml = QLabel("PAYMENT METHOD")
        ml.setStyleSheet("color: #334155; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
        v.addWidget(ml)

        self.method = QComboBox()
        self.method.addItems([
            "💵  Cash", "💳  Card", "🏦  Bank Transfer",
            "📱  Mobile Wallet", "📋  Other"
        ])
        self.method.setFixedHeight(50)
        self.method.setStyleSheet(self._combo_style())
        v.addWidget(self.method)

        self.amount_label = QLabel("CASH RECEIVED")
        self.amount_label.setStyleSheet("color: #334155; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
        v.addWidget(self.amount_label)

        self.cash = QDoubleSpinBox()
        self.cash.setMaximum(999999999)
        self.cash.setDecimals(2)
        self.cash.setValue(total)
        self.cash.setFixedHeight(50)
        self.cash.setStyleSheet("""
            QDoubleSpinBox {
                background: #FFFFFF; border: 2px solid #CBD5E1;
                border-radius: 10px; padding: 10px 16px;
                font-size: 16px; font-weight: 700; color: #0F172A;
            }
            QDoubleSpinBox:focus { border: 2px solid #4F46E5; }
        """)
        self.cash.valueChanged.connect(self._update_change)
        v.addWidget(self.cash)

        self.chg_box = QFrame()
        self.chg_box.setStyleSheet("background: #ECFDF5; border-radius: 10px;")
        chg_l = QHBoxLayout(self.chg_box)
        chg_l.setContentsMargins(16, 14, 16, 14)
        self.chg_title = QLabel("CHANGE")
        self.chg_title.setStyleSheet("color: #059669; font-size: 12px; font-weight: 800; letter-spacing: 0.5px;")
        chg_l.addWidget(self.chg_title)
        chg_l.addStretch()
        self.chg_val = QLabel(money(0))
        self.chg_val.setStyleSheet("color: #059669; font-weight: 900; font-size: 20px;")
        chg_l.addWidget(self.chg_val)
        v.addWidget(self.chg_box)

        self.customer_section = QFrame()
        self.customer_section.setVisible(False)
        cs = QVBoxLayout(self.customer_section)
        cs.setContentsMargins(0, 8, 0, 0)
        cs.setSpacing(12)

        cust_title = QLabel("👤  CUSTOMER DETAILS (Udhaar)")
        cust_title.setStyleSheet("""
            color: #92400E; font-size: 12px; font-weight: 800; letter-spacing: 1px;
            padding: 10px 12px; background: #FEF3C7; border-radius: 8px;
        """)
        cs.addWidget(cust_title)

        name_lbl = QLabel("Customer Name *")
        name_lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
        cs.addWidget(name_lbl)

        self.cust_name = QLineEdit()
        self.cust_name.setPlaceholderText("e.g., Ali Ahmed")
        self.cust_name.setFixedHeight(46)
        self.cust_name.setStyleSheet(self._input_style())
        cs.addWidget(self.cust_name)

        phone_lbl = QLabel("Phone Number *")
        phone_lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
        cs.addWidget(phone_lbl)

        self.cust_phone = QLineEdit()
        self.cust_phone.setPlaceholderText("e.g., 03001234567")
        self.cust_phone.setFixedHeight(46)
        self.cust_phone.setStyleSheet(self._input_style())
        cs.addWidget(self.cust_phone)

        addr_lbl = QLabel("Address (optional)")
        addr_lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
        cs.addWidget(addr_lbl)

        self.cust_address = QLineEdit()
        self.cust_address.setPlaceholderText("e.g., Shop #12, Main Bazaar")
        self.cust_address.setFixedHeight(46)
        self.cust_address.setStyleSheet(self._input_style())
        cs.addWidget(self.cust_address)

        v.addWidget(self.customer_section)
        v.addStretch()

        scroll.setWidget(body)
        main.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(28, 16, 28, 20)
        fl.setSpacing(12)

        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(52)
        cancel.setFixedWidth(140)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #0F172A;
                border: 2px solid #E2E8F0; border-radius: 10px;
                font-size: 14px; font-weight: 700;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }
        """)
        cancel.clicked.connect(self.reject)
        fl.addWidget(cancel)

        complete = QPushButton("✓  Complete Sale")
        complete.setFixedHeight(52)
        complete.setCursor(Qt.PointingHandCursor)
        complete.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF; border: none; border-radius: 10px;
                font-size: 15px; font-weight: 800;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        complete.clicked.connect(self._complete)
        fl.addWidget(complete, 1)

        main.addWidget(footer)

    def _combo_style(self):
        return """
            QComboBox {
                background: #FFFFFF; border: 2px solid #CBD5E1;
                border-radius: 10px; padding: 10px 16px;
                font-size: 14px; font-weight: 600; color: #0F172A;
            }
            QComboBox:hover { border: 2px solid #4F46E5; }
            QComboBox:focus { border: 2px solid #4F46E5; }
            QComboBox::drop-down { border: none; width: 40px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #4F46E5;
                margin-right: 14px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF; border: 2px solid #4F46E5;
                border-radius: 10px; padding: 6px; outline: none;
                selection-background-color: #EEF2FF; selection-color: #4F46E5;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 16px; border-radius: 6px;
                font-size: 13px; font-weight: 600; color: #0F172A; min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover { background: #EEF2FF; }
            QComboBox QAbstractItemView::item:selected {
                background: #4F46E5; color: #FFFFFF;
            }
        """

    def _input_style(self):
        return """
            QLineEdit {
                background: #FFFFFF; border: 2px solid #CBD5E1;
                border-radius: 10px; padding: 10px 14px;
                font-size: 13px; color: #0F172A;
            }
            QLineEdit:focus { border: 2px solid #F59E0B; }
        """

    def _on_type_changed(self, idx):
        is_partial = idx == 1
        self.customer_section.setVisible(is_partial)
        if is_partial:
            self.cash.setValue(0)
            self.amount_label.setText("AMOUNT PAID NOW (Rs.)")
        else:
            self.cash.setValue(self.total)
            self.amount_label.setText("CASH RECEIVED")

    def _update_change(self, val):
        if self.pay_type.currentIndex() == 0:
            change = max(0, val - self.total)
            self.chg_box.setStyleSheet("background: #ECFDF5; border-radius: 10px;")
            self.chg_title.setText("CHANGE")
            self.chg_title.setStyleSheet("color: #059669; font-size: 12px; font-weight: 800;")
            self.chg_val.setStyleSheet("color: #059669; font-weight: 900; font-size: 20px;")
            self.chg_val.setText(money(change))
        else:
            remaining = max(0, self.total - val)
            self.chg_box.setStyleSheet("background: #FEF3C7; border-radius: 10px;")
            self.chg_title.setText("REMAINING (UDHAAR)")
            self.chg_title.setStyleSheet("color: #92400E; font-size: 12px; font-weight: 800;")
            self.chg_val.setStyleSheet("color: #92400E; font-weight: 900; font-size: 20px;")
            self.chg_val.setText(money(remaining))

    def _complete(self):
        is_partial = self.pay_type.currentIndex() == 1

        if is_partial:
            if not self.cust_name.text().strip():
                QMessageBox.warning(self, "Missing Info", "Please enter customer name for udhaar.")
                self.cust_name.setFocus()
                return
            if not self.cust_phone.text().strip():
                QMessageBox.warning(self, "Missing Info", "Please enter customer phone for udhaar.")
                self.cust_phone.setFocus()
                return
            if self.cash.value() > self.total:
                QMessageBox.warning(self, "Invalid Amount", "Amount paid cannot exceed total.")
                return

        if not is_partial and "Cash" in self.method.currentText() and self.cash.value() < self.total:
            QMessageBox.warning(self, "Insufficient Cash", "Cash received is less than total.")
            return

        method_text = self.method.currentText()
        for emoji in ["💵  ", "💳  ", "🏦  ", "📱  ", "📋  "]:
            method_text = method_text.replace(emoji, "")

        self.result_data = {
            "is_partial": is_partial,
            "total": self.total,
            "amount_paid": self.cash.value(),
            "method": method_text,
            "customer_name": self.cust_name.text().strip(),
            "customer_phone": self.cust_phone.text().strip(),
            "customer_address": self.cust_address.text().strip(),
        }
        self.accept()


# =========================================================
# RECEIPT DIALOG
# =========================================================
class ReceiptDialog(QDialog):
    def __init__(self, invoice, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.setWindowTitle(f"Receipt — {invoice}")
        self.setFixedSize(420, 640)
        self.setStyleSheet(DIALOG_STYLE)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        self.receipt_text = QTextEdit()
        self.receipt_text.setReadOnly(True)
        self.receipt_text.setStyleSheet("""
            QTextEdit {
                background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 8px; padding: 16px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px; color: #0F172A;
            }
        """)
        v.addWidget(self.receipt_text, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        close = QPushButton("Close")
        close.setProperty("variant", "secondary")
        close.setFixedHeight(46)
        close.clicked.connect(self.accept)
        btn_row.addWidget(close)

        print_btn = QPushButton("🖨  Print")
        print_btn.setFixedHeight(46)
        print_btn.setStyleSheet("font-size: 13px; font-weight: 700;")
        print_btn.clicked.connect(self._print)
        btn_row.addWidget(print_btn, 1)

        v.addLayout(btn_row)

        self._generate_receipt()

    def _generate_receipt(self):
        with SessionLocal() as s:
            sale = s.query(Sale).filter_by(invoice=self.invoice).first()
            if not sale:
                self.receipt_text.setText("Receipt not found.")
                return

            settings = {st.key: st.value for st in s.query(Setting).all()}
            shop = settings.get("shop_name", "My Retail Store")
            addr = settings.get("shop_address", "")
            phone = settings.get("shop_phone", "")
            footer = settings.get("receipt_footer", "Thank you!")

            customer_name = ""
            customer_phone = ""
            if sale.credit_customer_id:
                cust = s.get(CreditCustomer, sale.credit_customer_id)
                if cust:
                    customer_name = cust.name
                    customer_phone = cust.phone

            cashier = s.get(User, sale.cashier_id)
            cashier_name = cashier.username if cashier else "N/A"

            W = 42
            lines = []
            lines.append(shop.center(W))
            if addr:
                lines.append(addr.center(W))
            if phone:
                lines.append(f"Tel: {phone}".center(W))
            lines.append("=" * W)
            lines.append(f"Invoice : {sale.invoice}")
            lines.append(f"Date    : {sale.created_at:%d-%b-%Y %I:%M %p}")
            lines.append(f"Cashier : {cashier_name}")
            if customer_name:
                lines.append(f"Customer: {customer_name}")
                if customer_phone:
                    lines.append(f"Phone   : {customer_phone}")
            lines.append("-" * W)
            lines.append(f"{'Item':<20}{'Qty':>4}{'Price':>8}{'Total':>10}")
            lines.append("-" * W)

            for it in sale.items:
                name = it.product_name[:20]
                lines.append(f"{name:<20}{it.quantity:>4.0f}{it.unit_price:>8.0f}{it.subtotal:>10.0f}")

            lines.append("-" * W)
            lines.append(f"{'SUBTOTAL':<32}{sale.subtotal:>10.2f}")
            if sale.discount:
                lines.append(f"{'DISCOUNT':<32}{sale.discount:>10.2f}")
            lines.append(f"{'TOTAL':<32}{sale.total:>10.2f}")
            lines.append("-" * W)
            lines.append(f"{'Payment':<32}{sale.payment_method:>10}")

            if sale.credit_customer_id and sale.credit_amount > 0:
                lines.append(f"{'Paid Now':<32}{sale.cash_received:>10.2f}")
                lines.append(f"{'** UDHAAR (Credit)':<32}{sale.credit_amount:>10.2f}")
                lines.append("-" * W)
                lines.append("This amount added to customer credit")
                lines.append("Please pay on next visit.")

            if sale.change_amount > 0:
                lines.append(f"{'Change':<32}{sale.change_amount:>10.2f}")

            lines.append("=" * W)
            lines.append(footer.center(W))
            lines.append("")
            lines.append("Powered by Retail POS".center(W))

            self.receipt_text.setPlainText("\n".join(lines))

    def _print(self):
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.Accepted:
            self.receipt_text.print_(printer)


# =========================================================
# POS WIDGET
# =========================================================
class POSWidget(QWidget):
    def __init__(self, user, refresh_dashboard=None):
        super().__init__()
        self.user = user
        self.cart = []
        self.refresh_dashboard = refresh_dashboard
        self.current_category = "All"
        self.all_products = []

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Category rail
        cat_bar = QFrame()
        cat_bar.setObjectName("CategoryBar")
        cat_bar.setStyleSheet(CATEGORY_STYLE)
        cat_bar.setFixedWidth(78)

        self.cat_layout = QVBoxLayout(cat_bar)
        self.cat_layout.setContentsMargins(6, 12, 6, 12)
        self.cat_layout.setSpacing(4)

        self.cat_group = QButtonGroup(self)
        self.cat_group.setExclusive(True)
        self._build_category_bar()
        self.cat_layout.addStretch()
        root.addWidget(cat_bar)

        # Center
        center = QWidget()
        center.setStyleSheet("background: #F1F5F9;")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet("background: #F1F5F9;")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(18, 14, 18, 6)

        self.section_title = QLabel("All Products")
        self.section_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0F172A;")
        tb.addWidget(self.section_title)
        tb.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        tb.addWidget(self.count_lbl)
        center_layout.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: #F1F5F9; border: none; }")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: #F1F5F9;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(18, 6, 18, 18)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        center_layout.addWidget(self.scroll, 1)
        root.addWidget(center, 1)

        # Cart panel
        self.cart_panel = QFrame()
        self.cart_panel.setObjectName("CartPanel")
        self.cart_panel.setStyleSheet(CART_STYLE)
        self.cart_panel.setFixedWidth(360)

        cp_layout = QVBoxLayout(self.cart_panel)
        cp_layout.setContentsMargins(0, 0, 0, 0)
        cp_layout.setSpacing(0)

        cart_header = QFrame()
        cart_header.setObjectName("CartHeader")
        cart_header.setStyleSheet(CART_STYLE)
        ch = QHBoxLayout(cart_header)
        ch.setContentsMargins(18, 16, 18, 16)
        ch.setSpacing(8)

        info = QVBoxLayout()
        info.setSpacing(2)
        ct = QLabel("Current Sale")
        ct.setObjectName("CartTitle")
        ct.setStyleSheet(CART_STYLE)
        cs = QLabel("Walk-in Customer")
        cs.setObjectName("CartSubtitle")
        cs.setStyleSheet(CART_STYLE)
        info.addWidget(ct)
        info.addWidget(cs)
        ch.addLayout(info)
        ch.addStretch()

        held_btn = QPushButton("Held")
        held_btn.setProperty("variant", "ghost")
        held_btn.setStyleSheet(CART_STYLE)
        held_btn.setCursor(Qt.PointingHandCursor)
        held_btn.clicked.connect(self.open_held_sales)
        ch.addWidget(held_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("variant", "ghost")
        clear_btn.setStyleSheet(CART_STYLE)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_cart)
        ch.addWidget(clear_btn)

        cp_layout.addWidget(cart_header)

        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        self.cart_items_container = QWidget()
        self.cart_items_container.setStyleSheet("background: #FFFFFF;")
        self.cart_items_layout = QVBoxLayout(self.cart_items_container)
        self.cart_items_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_items_layout.setSpacing(0)
        self.cart_items_layout.addStretch()

        self.cart_scroll.setWidget(self.cart_items_container)
        cp_layout.addWidget(self.cart_scroll, 1)

        self.empty_lbl = QLabel("🛒\n\nCart is empty\n\nClick any product to add it")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setStyleSheet(
            "color: #94A3B8; font-size: 12px; background: #FFFFFF; padding: 60px 20px; line-height: 1.8;"
        )
        cp_layout.addWidget(self.empty_lbl, 1)

        footer = QFrame()
        footer.setObjectName("CartFooter")
        footer.setStyleSheet(CART_STYLE)
        f = QVBoxLayout(footer)
        f.setContentsMargins(18, 16, 18, 18)
        f.setSpacing(10)

        sub_row = QHBoxLayout()
        sl = QLabel("Subtotal")
        sl.setObjectName("SubLabel")
        sl.setStyleSheet(CART_STYLE)
        sub_row.addWidget(sl)
        sub_row.addStretch()
        self.subtotal_lbl = QLabel("Rs. 0")
        self.subtotal_lbl.setObjectName("SubValue")
        self.subtotal_lbl.setStyleSheet(CART_STYLE)
        sub_row.addWidget(self.subtotal_lbl)
        f.addLayout(sub_row)

        cnt_row = QHBoxLayout()
        cl = QLabel("Items")
        cl.setObjectName("SubLabel")
        cl.setStyleSheet(CART_STYLE)
        cnt_row.addWidget(cl)
        cnt_row.addStretch()
        self.item_count_lbl = QLabel("0")
        self.item_count_lbl.setObjectName("SubValue")
        self.item_count_lbl.setStyleSheet(CART_STYLE)
        cnt_row.addWidget(self.item_count_lbl)
        f.addLayout(cnt_row)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #E2E8F0;")
        f.addWidget(div)

        total_row = QHBoxLayout()
        tl = QLabel("TOTAL")
        tl.setObjectName("TotalLabel")
        tl.setStyleSheet(CART_STYLE)
        total_row.addWidget(tl)
        total_row.addStretch()
        self.total_value = QLabel("Rs. 0")
        self.total_value.setObjectName("TotalValue")
        self.total_value.setStyleSheet(CART_STYLE)
        total_row.addWidget(self.total_value)
        f.addLayout(total_row)

        f.addSpacing(4)

        hold = QPushButton("Hold Sale")
        hold.setProperty("variant", "secondary")
        hold.setFixedHeight(44)
        hold.setCursor(Qt.PointingHandCursor)
        hold.clicked.connect(self.hold_sale)
        f.addWidget(hold)

        self.checkout_btn = QPushButton("CHECKOUT  →")
        self.checkout_btn.setObjectName("CheckoutBtn")
        self.checkout_btn.setStyleSheet(CART_STYLE)
        self.checkout_btn.setFixedHeight(56)
        self.checkout_btn.setCursor(Qt.PointingHandCursor)
        self.checkout_btn.clicked.connect(self.checkout)
        f.addWidget(self.checkout_btn)

        cp_layout.addWidget(footer)

        root.addWidget(self.cart_panel)

        self.load_products()
        self.render_cart()

    def _build_category_bar(self):
        with SessionLocal() as s:
            cats = ["All"] + [c.name for c in s.query(Category).order_by(Category.name).all()]

        for cat in cats:
            icon = CATEGORY_ICONS.get(cat, "●")
            btn = CategoryButton(icon, cat)
            btn.setChecked(cat == "All")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, c=cat: self.filter_category(c))
            self.cat_group.addButton(btn)
            self.cat_layout.addWidget(btn, 0, Qt.AlignHCenter)

    def filter_category(self, cat):
        self.current_category = cat
        self.section_title.setText(cat if cat != "All" else "All Products")
        self.load_products()

    def load_products(self):
        with SessionLocal() as s:
            q = s.query(Product).filter_by(active=True)
            if self.current_category != "All":
                cat = s.query(Category).filter_by(name=self.current_category).first()
                if cat:
                    q = q.filter(Product.category_id == cat.id)
            self.all_products = q.order_by(Product.name).limit(500).all()

        self._clear_grid()

        cols = 4
        for i, p in enumerate(self.all_products):
            card = ProductCard(p)
            card.clicked.connect(self.add_product)
            self.grid_layout.addWidget(card, i // cols, i % cols)

        self.count_lbl.setText(f"{len(self.all_products)} products")

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _get_price_for_qty(self, product, qty):
        if (product.wholesale_price > 0 and
                product.wholesale_min_qty > 0 and
                qty >= product.wholesale_min_qty):
            return product.wholesale_price, True
        return product.selling_price, False

    def add_product(self, pid):
        with SessionLocal() as s:
            p = s.get(Product, pid)
            if not p:
                return
            if p.stock_quantity <= 0:
                QMessageBox.warning(self, "Out of Stock", f"{p.name} is out of stock.")
                return

            for x in self.cart:
                if x["id"] == pid:
                    new_qty = x["qty"] + 1
                    if new_qty > p.stock_quantity:
                        QMessageBox.warning(self, "Stock Limit",
                                            f"Only {p.stock_quantity:.0f} units available.")
                        return
                    x["qty"] = new_qty
                    new_price, is_whole = self._get_price_for_qty(p, new_qty)
                    x["price"] = new_price
                    x["is_wholesale"] = is_whole
                    self.render_cart()
                    return

            price, is_whole = self._get_price_for_qty(p, 1)
            self.cart.append({
                "id": p.id, "name": p.name,
                "price": price, "qty": 1,
                "is_wholesale": is_whole,
            })
        self.render_cart()

    def render_cart(self):
        while self.cart_items_layout.count() > 1:
            item = self.cart_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subtotal = 0
        total_items = 0
        for i, x in enumerate(self.cart):
            subtotal += x["price"] * x["qty"]
            total_items += x["qty"]
            w = CartItemWidget(x)
            w.qty_changed.connect(self._update_qty)
            w.removed.connect(self._remove_item)
            self.cart_items_layout.insertWidget(i, w)

        self.subtotal_lbl.setText(money(subtotal))
        self.total_value.setText(money(subtotal))
        self.item_count_lbl.setText(f"{int(total_items)}")

        has_items = len(self.cart) > 0
        self.empty_lbl.setVisible(not has_items)
        self.cart_scroll.setVisible(has_items)
        self.checkout_btn.setEnabled(has_items)

    def _update_qty(self, pid, new_qty):
        with SessionLocal() as s:
            p = s.get(Product, pid)
            if not p:
                return
            max_stock = p.stock_quantity

            for x in self.cart:
                if x["id"] == pid:
                    if new_qty <= 0:
                        self.cart.remove(x)
                    else:
                        if new_qty > max_stock:
                            QMessageBox.warning(self, "Stock Limit",
                                                f"Only {max_stock:.0f} units available.")
                            return
                        x["qty"] = new_qty
                        new_price, is_whole = self._get_price_for_qty(p, new_qty)
                        x["price"] = new_price
                        x["is_wholesale"] = is_whole
                    break
        self.render_cart()

    def _remove_item(self, pid):
        self.cart = [x for x in self.cart if x["id"] != pid]
        self.render_cart()

    def clear_cart(self):
        if not self.cart:
            return
        if QMessageBox.question(self, "Clear Cart", "Remove all items from cart?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self.cart = []
        self.render_cart()

    def hold_sale(self):
        if not self.cart:
            QMessageBox.information(self, "Empty Cart", "Add products first.")
            return
        note, ok = QInputDialog.getText(self, "Hold Sale", "Note (optional):")
        if not ok:
            return
        with SessionLocal() as s:
            ref = f"HOLD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            h = HeldSale(reference=ref, note=note or "")
            s.add(h)
            s.flush()
            for x in self.cart:
                s.add(HeldSaleItem(
                    held_sale_id=h.id, product_id=x["id"],
                    product_name=x["name"], quantity=x["qty"],
                    unit_price=x["price"], subtotal=x["qty"] * x["price"]
                ))
            s.commit()
        self.cart = []
        self.render_cart()
        QMessageBox.information(self, "Sale Held", f"Saved as {ref}\n\nClick 'Held' to resume.")

    def open_held_sales(self):
        dlg = HeldSalesDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.selected:
            self.resume_held_sale(dlg.selected)

    def resume_held_sale(self, held_id):
        if self.cart:
            if QMessageBox.question(self, "Resume Sale",
                                    "Current cart has items. Replace with held sale?",
                                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        with SessionLocal() as s:
            h = s.get(HeldSale, held_id)
            if not h:
                return
            items = s.query(HeldSaleItem).filter_by(held_sale_id=held_id).all()
            self.cart = []
            for it in items:
                p = s.get(Product, it.product_id)
                if p:
                    price, is_whole = self._get_price_for_qty(p, it.quantity)
                    self.cart.append({
                        "id": p.id, "name": p.name,
                        "price": price, "qty": it.quantity,
                        "is_wholesale": is_whole,
                    })
            s.delete(h)
            s.commit()
        self.render_cart()
        QMessageBox.information(self, "Resumed", "Held sale loaded into cart.")

    def checkout(self):
        if not self.cart:
            return

        total = sum(x["qty"] * x["price"] for x in self.cart)

        dlg = CheckoutDialog(total, self)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        data = dlg.result_data
        is_partial = data["is_partial"]
        amount_paid = data["amount_paid"]
        method = data["method"]
        cust_name = data["customer_name"]
        cust_phone = data["customer_phone"]
        cust_addr = data["customer_address"]

        credit_amount = 0
        if is_partial:
            credit_amount = total - amount_paid

        with SessionLocal() as s:
            try:
                inv = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

                credit_customer_id = None
                if is_partial and cust_name:
                    existing = s.query(CreditCustomer).filter_by(phone=cust_phone).first()
                    if existing:
                        credit_customer_id = existing.id
                        existing.name = cust_name
                        if cust_addr:
                            existing.address = cust_addr
                    else:
                        cc = CreditCustomer(
                            name=cust_name, phone=cust_phone, address=cust_addr,
                            total_credit=0, total_paid=0, balance=0,
                        )
                        s.add(cc)
                        s.flush()
                        credit_customer_id = cc.id

                sale = Sale(
                    invoice=inv, cashier_id=self.user[0],
                    subtotal=total, total=total,
                    payment_method=method,
                    cash_received=amount_paid,
                    change_amount=max(0, amount_paid - total) if not is_partial else 0,
                    credit_customer_id=credit_customer_id,
                    credit_amount=credit_amount,
                )
                s.add(sale)
                s.flush()

                for x in self.cart:
                    p = s.get(Product, x["id"])
                    if p.stock_quantity < x["qty"]:
                        raise ValueError(f"Insufficient stock: {p.name}")
                    old = p.stock_quantity
                    p.stock_quantity -= x["qty"]
                    s.add(InventoryMovement(
                        product_id=p.id, change=-x["qty"],
                        previous_stock=old, new_stock=p.stock_quantity,
                        reason=f"Sale {inv}"
                    ))
                    s.add(SaleItem(
                        sale_id=sale.id, product_id=p.id,
                        product_name=p.name, quantity=x["qty"],
                        unit_price=x["price"], subtotal=x["qty"] * x["price"]
                    ))

                if is_partial and credit_customer_id:
                    cc = s.get(CreditCustomer, credit_customer_id)
                    cc.total_credit += credit_amount
                    cc.balance = cc.total_credit - cc.total_paid

                    s.add(CreditTransaction(
                        customer_id=credit_customer_id,
                        sale_id=sale.id,
                        type="credit",
                        amount=credit_amount,
                        description=f"Udhaar from invoice {inv}",
                        balance_after=cc.balance,
                    ))

                s.commit()
            except Exception as e:
                s.rollback()
                QMessageBox.critical(self, "Checkout Failed", str(e))
                return

        self.cart = []
        self.render_cart()
        self.load_products()

        if self.refresh_dashboard:
            self.refresh_dashboard()

        ReceiptDialog(inv, self).exec()


# =========================================================
# PRODUCTS WIDGET
# =========================================================
class ProductsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_ids = set()
        self.all_checkboxes = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Products")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
        header.addWidget(title)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 600; padding-left: 12px;")
        header.addWidget(self.count_lbl)
        header.addStretch()

        self.selected_lbl = QLabel("")
        self.selected_lbl.setStyleSheet("""
            color: #4F46E5; font-size: 13px; font-weight: 700;
            padding: 8px 14px; background: #EEF2FF; border-radius: 6px;
        """)
        self.selected_lbl.setVisible(False)
        header.addWidget(self.selected_lbl)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setFixedHeight(40)
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.setVisible(False)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #4F46E5;
                border: 2px solid #4F46E5; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 8px 16px;
            }
            QPushButton:hover { background: #EEF2FF; }
        """)
        self.select_all_btn.clicked.connect(self.select_all)
        header.addWidget(self.select_all_btn)

        self.clear_sel_btn = QPushButton("Clear")
        self.clear_sel_btn.setFixedHeight(40)
        self.clear_sel_btn.setCursor(Qt.PointingHandCursor)
        self.clear_sel_btn.setVisible(False)
        self.clear_sel_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; color: #64748B;
                border: 2px solid #E2E8F0; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 8px 16px;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #94A3B8; }
        """)
        self.clear_sel_btn.clicked.connect(self.clear_selection)
        header.addWidget(self.clear_sel_btn)

        self.bulk_delete_btn = QPushButton("Delete Selected")
        self.bulk_delete_btn.setFixedHeight(40)
        self.bulk_delete_btn.setCursor(Qt.PointingHandCursor)
        self.bulk_delete_btn.setVisible(False)
        self.bulk_delete_btn.setStyleSheet("""
            QPushButton {
                background: #DC2626; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: 700; padding: 8px 18px;
            }
            QPushButton:hover { background: #B91C1C; }
        """)
        self.bulk_delete_btn.clicked.connect(self.bulk_delete)
        header.addWidget(self.bulk_delete_btn)

        add = QPushButton("+ Add Product")
        add.setFixedHeight(40)
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add)
        header.addWidget(add)

        imp = QPushButton("Import")
        imp.setProperty("variant", "secondary")
        imp.setFixedHeight(40)
        imp.clicked.connect(self.import_file)
        header.addWidget(imp)

        exp = QPushButton("Export")
        exp.setProperty("variant", "secondary")
        exp.setFixedHeight(40)
        exp.clicked.connect(self.export_file)
        header.addWidget(exp)

        root.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search products by name, barcode, or SKU...")
        self.search.setFixedHeight(44)
        self.search.textChanged.connect(self.load)
        root.addWidget(self.search)

        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels([
            "SELECT", "ID", "PRODUCT", "BARCODE", "SKU",
            "BUY", "RETAIL", "WHOLESALE", "W. QTY",
            "STOCK", "MIN", "ACTIONS"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 55)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 70)
        self.table.setColumnWidth(9, 70)
        self.table.setColumnWidth(10, 60)
        self.table.setColumnWidth(11, 160)

        root.addWidget(self.table, 1)
        self.load()

    def load(self):
        q = self.search.text().strip()
        with SessionLocal() as s:
            query = s.query(Product).order_by(Product.name)
            if q:
                query = query.filter(
                    (Product.name.ilike(f"%{q}%")) |
                    (Product.barcode.ilike(f"%{q}%")) |
                    (Product.sku.ilike(f"%{q}%"))
                )
            ps = query.limit(2000).all()

        self.table.setRowCount(0)
        self.selected_ids.clear()
        self.all_checkboxes.clear()
        self._update_bulk_bar()

        for p in ps:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 56)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)

            cb = QCheckBox()
            cb.setCursor(Qt.PointingHandCursor)
            cb.setStyleSheet("""
                QCheckBox::indicator {
                    width: 20px; height: 20px;
                    border: 2px solid #CBD5E1; border-radius: 5px;
                    background: #FFFFFF;
                }
                QCheckBox::indicator:hover { border: 2px solid #4F46E5; }
                QCheckBox::indicator:checked {
                    background: #4F46E5; border: 2px solid #4F46E5;
                }
            """)
            cb.stateChanged.connect(lambda state, pid=p.id: self._on_row_check(state, pid))
            cb_layout.addWidget(cb)
            self.table.setCellWidget(r, 0, cb_widget)
            self.all_checkboxes[p.id] = cb

            id_item = QTableWidgetItem(str(p.id))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setForeground(QColor("#64748B"))
            self.table.setItem(r, 1, id_item)

            name_item = QTableWidgetItem(p.name)
            fnt = name_item.font(); fnt.setBold(True); name_item.setFont(fnt)
            self.table.setItem(r, 2, name_item)

            self.table.setItem(r, 3, QTableWidgetItem(p.barcode or "—"))

            sku_item = QTableWidgetItem(p.sku or "—")
            sku_item.setForeground(QColor("#64748B"))
            self.table.setItem(r, 4, sku_item)

            self.table.setItem(r, 5, QTableWidgetItem(money(p.purchase_price)))

            retail_item = QTableWidgetItem(money(p.selling_price))
            retail_item.setForeground(QColor("#0F172A"))
            fnt2 = retail_item.font(); fnt2.setBold(True); retail_item.setFont(fnt2)
            self.table.setItem(r, 6, retail_item)

            if p.wholesale_price > 0:
                w_item = QTableWidgetItem(money(p.wholesale_price))
                w_item.setForeground(QColor("#059669"))
                fnt3 = w_item.font(); fnt3.setBold(True); w_item.setFont(fnt3)
                self.table.setItem(r, 7, w_item)
            else:
                w_item = QTableWidgetItem("—")
                w_item.setForeground(QColor("#94A3B8"))
                w_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 7, w_item)

            if p.wholesale_min_qty > 0:
                wq_item = QTableWidgetItem(f"{p.wholesale_min_qty:.0f}+")
                wq_item.setForeground(QColor("#059669"))
                wq_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 8, wq_item)
            else:
                wq_item = QTableWidgetItem("—")
                wq_item.setForeground(QColor("#94A3B8"))
                wq_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, 8, wq_item)

            stock_item = QTableWidgetItem(f"{p.stock_quantity:.0f}")
            stock_item.setTextAlignment(Qt.AlignCenter)
            if p.stock_quantity <= 0:
                stock_item.setForeground(QColor("#DC2626"))
                fnt4 = stock_item.font(); fnt4.setBold(True); stock_item.setFont(fnt4)
            elif p.stock_quantity <= p.minimum_stock:
                stock_item.setForeground(QColor("#D97706"))
                fnt4 = stock_item.font(); fnt4.setBold(True); stock_item.setFont(fnt4)
            else:
                stock_item.setForeground(QColor("#059669"))
            self.table.setItem(r, 9, stock_item)

            min_item = QTableWidgetItem(f"{p.minimum_stock:.0f}")
            min_item.setTextAlignment(Qt.AlignCenter)
            min_item.setForeground(QColor("#64748B"))
            self.table.setItem(r, 10, min_item)

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 4, 4, 4)
            al.setSpacing(8)
            al.setAlignment(Qt.AlignCenter)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(34); edit_btn.setFixedWidth(62)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #EEF2FF; color: #4F46E5;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 700;
                }
                QPushButton:hover { background: #4F46E5; color: white; }
            """)
            edit_btn.clicked.connect(lambda _, pid=p.id: self.edit_product(pid))
            al.addWidget(edit_btn)

            del_btn = QPushButton("Delete")
            del_btn.setFixedHeight(34); del_btn.setFixedWidth(70)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #FEF2F2; color: #DC2626;
                    border: none; border-radius: 6px;
                    font-size: 12px; font-weight: 700;
                }
                QPushButton:hover { background: #DC2626; color: white; }
            """)
            del_btn.clicked.connect(lambda _, pid=p.id: self.delete_product(pid))
            al.addWidget(del_btn)

            self.table.setCellWidget(r, 11, actions)

        self.count_lbl.setText(f"{len(ps)} products")

    def _on_row_check(self, state, pid):
        if state == 2:
            self.selected_ids.add(pid)
        else:
            self.selected_ids.discard(pid)
        self._update_bulk_bar()

    def _update_bulk_bar(self):
        count = len(self.selected_ids)
        total = self.table.rowCount()
        if count > 0:
            self.selected_lbl.setText(f"●  {count} selected")
            self.selected_lbl.setVisible(True)
            self.bulk_delete_btn.setVisible(True)
            self.clear_sel_btn.setVisible(True)
            self.select_all_btn.setVisible(total > count)
        else:
            self.selected_lbl.setVisible(False)
            self.bulk_delete_btn.setVisible(False)
            self.clear_sel_btn.setVisible(False)
            self.select_all_btn.setVisible(total > 0)

    def select_all(self):
        for pid, cb in self.all_checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            self.selected_ids.add(pid)
        self._update_bulk_bar()

    def clear_selection(self):
        for pid, cb in self.all_checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self.selected_ids.clear()
        self._update_bulk_bar()

    def bulk_delete(self):
        if not self.selected_ids:
            QMessageBox.information(self, "No Selection", "Please select products to delete.")
            return

        count = len(self.selected_ids)

        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Products")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"<b>Delete {count} products?</b>")
        msg.setInformativeText(
            "Products with sales history will be marked as inactive.\n\n"
            "⚠️  This action cannot be undone."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        if msg.exec() != QMessageBox.Yes:
            return

        try:
            deleted = 0
            skipped = 0
            with SessionLocal() as s:
                for pid in list(self.selected_ids):
                    p = s.get(Product, pid)
                    if not p:
                        continue
                    has_sales = s.query(SaleItem).filter_by(product_id=pid).first()
                    if has_sales:
                        p.active = False
                        skipped += 1
                    else:
                        s.delete(p)
                        deleted += 1
                s.commit()

            self.selected_ids.clear()
            self.load()

            info_msg = f"✅ {deleted} products deleted."
            if skipped > 0:
                info_msg += f"\n\n⚠️  {skipped} products marked inactive (sales history)."
            QMessageBox.information(self, "Bulk Delete Complete", info_msg)
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", str(e))

    def delete_product(self, pid):
        with SessionLocal() as s:
            p = s.get(Product, pid)
            if not p:
                QMessageBox.warning(self, "Not Found", "Product not found.")
                return
            name = p.name

        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Product")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(f"<b>Delete '{name}'?</b>")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        if msg.exec() != QMessageBox.Yes:
            return

        try:
            with SessionLocal() as s:
                p = s.get(Product, pid)
                if not p:
                    return
                has_sales = s.query(SaleItem).filter_by(product_id=pid).first()
                if has_sales:
                    p.active = False
                    s.commit()
                    QMessageBox.information(self, "Marked Inactive",
                                            f"'{name}' has sales history, marked inactive.")
                else:
                    s.delete(p)
                    s.commit()
                    QMessageBox.information(self, "Deleted", f"'{name}' deleted.")
            self.load()
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", str(e))

    def edit_product(self, pid):
        with SessionLocal() as s:
            p = s.get(Product, pid)
            if not p:
                return
            data = {
                "name": p.name, "barcode": p.barcode, "sku": p.sku,
                "purchase_price": p.purchase_price,
                "selling_price": p.selling_price,
                "wholesale_price": p.wholesale_price,
                "wholesale_min_qty": p.wholesale_min_qty,
                "stock_quantity": p.stock_quantity,
                "minimum_stock": p.minimum_stock,
            }

        d = QDialog(self)
        d.setWindowTitle(f"Edit Product")
        d.setFixedWidth(520); d.setFixedHeight(720)
        d.setStyleSheet(DIALOG_STYLE)

        main = QVBoxLayout(d)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        h = QFrame()
        h.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        hl = QVBoxLayout(h)
        hl.setContentsMargins(28, 22, 28, 16)
        t = QLabel("Edit Product")
        t.setObjectName("DialogTitle"); t.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(t)
        s_lbl = QLabel(f"Editing: {data['name']}")
        s_lbl.setObjectName("DialogSub"); s_lbl.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(s_lbl)
        main.addWidget(h)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        body = QWidget()
        body.setStyleSheet("background: #FFFFFF;")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(28, 20, 28, 20); bv.setSpacing(12)

        fields = {}

        def add_field(label, key, value=""):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
            bv.addWidget(lbl)
            w = QLineEdit()
            w.setText(str(value) if value else "")
            w.setFixedHeight(44)
            w.setStyleSheet("""
                QLineEdit {
                    background: #FFFFFF; border: 2px solid #CBD5E1;
                    border-radius: 10px; padding: 10px 14px;
                    font-size: 13px;
                }
                QLineEdit:focus { border: 2px solid #4F46E5; }
            """)
            bv.addWidget(w)
            fields[key] = w

        add_field("Product Name *", "name", data["name"])
        add_field("Barcode", "barcode", data["barcode"])
        add_field("SKU", "sku", data["sku"])

        section = QLabel("💰  PRICING")
        section.setStyleSheet("""
            color: #4F46E5; font-size: 12px; font-weight: 800;
            letter-spacing: 1px; padding: 10px 12px;
            background: #EEF2FF; border-radius: 8px;
        """)
        bv.addWidget(section)

        add_field("Purchase Price", "purchase_price", f"{data['purchase_price']:.0f}")
        add_field("Retail Price *", "selling_price", f"{data['selling_price']:.0f}")
        add_field("Wholesale Price", "wholesale_price", f"{data['wholesale_price']:.0f}")
        add_field("Wholesale Min Qty", "wholesale_min_qty", f"{data['wholesale_min_qty']:.0f}")

        section2 = QLabel("📦  STOCK")
        section2.setStyleSheet("""
            color: #059669; font-size: 12px; font-weight: 800;
            letter-spacing: 1px; padding: 10px 12px;
            background: #ECFDF5; border-radius: 8px;
        """)
        bv.addWidget(section2)

        add_field("Stock Quantity *", "stock_quantity", f"{data['stock_quantity']:.0f}")
        add_field("Minimum Stock", "minimum_stock", f"{data['minimum_stock']:.0f}")

        bv.addStretch()
        scroll.setWidget(body)
        main.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(28, 16, 28, 20); fl.setSpacing(12)

        cancel = QPushButton("Cancel")
        cancel.setProperty("variant", "secondary")
        cancel.setFixedHeight(48); cancel.setFixedWidth(120)
        cancel.clicked.connect(d.reject)
        fl.addWidget(cancel)

        save = QPushButton("💾  Save Changes")
        save.setFixedHeight(48)
        save.clicked.connect(d.accept)
        fl.addWidget(save, 1)

        main.addWidget(footer)

        if d.exec() != QDialog.Accepted:
            return

        try:
            name = fields["name"].text().strip()
            if not name:
                QMessageBox.warning(self, "Missing Info", "Product name required.")
                return

            with SessionLocal() as s:
                p = s.get(Product, pid)
                if not p:
                    return
                p.name = name
                p.barcode = fields["barcode"].text().strip()
                p.sku = fields["sku"].text().strip()
                p.purchase_price = float(fields["purchase_price"].text() or 0)
                p.selling_price = float(fields["selling_price"].text() or 0)
                p.wholesale_price = float(fields["wholesale_price"].text() or 0)
                p.wholesale_min_qty = float(fields["wholesale_min_qty"].text() or 0)
                p.stock_quantity = float(fields["stock_quantity"].text() or 0)
                p.minimum_stock = float(fields["minimum_stock"].text() or 0)
                s.commit()

            self.load()
            QMessageBox.information(self, "Updated", f"'{name}' updated.")
        except Exception as e:
            QMessageBox.critical(self, "Update Failed", str(e))

    def add(self):
        d = QDialog(self)
        d.setWindowTitle("Add Product")
        d.setFixedWidth(520); d.setFixedHeight(720)
        d.setStyleSheet(DIALOG_STYLE)

        main = QVBoxLayout(d)
        main.setContentsMargins(0, 0, 0, 0); main.setSpacing(0)

        h = QFrame()
        h.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E2E8F0;")
        hl = QVBoxLayout(h)
        hl.setContentsMargins(28, 22, 28, 16)
        t = QLabel("Add Product")
        t.setObjectName("DialogTitle"); t.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(t)
        s = QLabel("Enter product details and pricing")
        s.setObjectName("DialogSub"); s.setStyleSheet(DIALOG_STYLE)
        hl.addWidget(s)
        main.addWidget(h)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        body = QWidget()
        body.setStyleSheet("background: #FFFFFF;")
        bv = QVBoxLayout(body)
        bv.setContentsMargins(28, 20, 28, 20); bv.setSpacing(12)

        fields = {}

        def add_field(label, key, placeholder=""):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
            bv.addWidget(lbl)
            w = QLineEdit()
            w.setPlaceholderText(placeholder)
            w.setFixedHeight(44)
            w.setStyleSheet("""
                QLineEdit {
                    background: #FFFFFF; border: 2px solid #CBD5E1;
                    border-radius: 10px; padding: 10px 14px;
                    font-size: 13px;
                }
                QLineEdit:focus { border: 2px solid #4F46E5; }
            """)
            bv.addWidget(w)
            fields[key] = w

        add_field("Product Name *", "name", "e.g., Sugar 1kg")
        add_field("Barcode", "barcode", "e.g., 1000001")
        add_field("SKU", "sku", "e.g., GRC-0001")

        section = QLabel("💰  PRICING")
        section.setStyleSheet("""
            color: #4F46E5; font-size: 12px; font-weight: 800;
            letter-spacing: 1px; padding: 10px 12px;
            background: #EEF2FF; border-radius: 8px;
        """)
        bv.addWidget(section)

        add_field("Purchase Price", "purchase_price", "Cost price")
        add_field("Retail Price *", "selling_price", "Regular selling price")
        add_field("Wholesale Price", "wholesale_price", "Leave 0 if not applicable")
        add_field("Wholesale Min Qty", "wholesale_min_qty", "e.g., 6")

        section2 = QLabel("📦  STOCK")
        section2.setStyleSheet("""
            color: #059669; font-size: 12px; font-weight: 800;
            letter-spacing: 1px; padding: 10px 12px;
            background: #ECFDF5; border-radius: 8px;
        """)
        bv.addWidget(section2)

        add_field("Stock Quantity *", "stock_quantity", "Current stock")
        add_field("Minimum Stock", "minimum_stock", "Alert threshold")

        bv.addStretch()
        scroll.setWidget(body)
        main.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(28, 16, 28, 20); fl.setSpacing(12)

        cancel = QPushButton("Cancel")
        cancel.setProperty("variant", "secondary")
        cancel.setFixedHeight(48); cancel.setFixedWidth(120)
        cancel.clicked.connect(d.reject)
        fl.addWidget(cancel)

        save = QPushButton("💾  Save Product")
        save.setFixedHeight(48)
        save.clicked.connect(d.accept)
        fl.addWidget(save, 1)

        main.addWidget(footer)

        if d.exec() != QDialog.Accepted:
            return

        try:
            name = fields["name"].text().strip()
            if not name:
                QMessageBox.warning(self, "Missing Info", "Product name required.")
                return

            with SessionLocal() as s:
                s.add(Product(
                    name=name,
                    barcode=fields["barcode"].text().strip(),
                    sku=fields["sku"].text().strip(),
                    purchase_price=float(fields["purchase_price"].text() or 0),
                    selling_price=float(fields["selling_price"].text() or 0),
                    wholesale_price=float(fields["wholesale_price"].text() or 0),
                    wholesale_min_qty=float(fields["wholesale_min_qty"].text() or 0),
                    stock_quantity=float(fields["stock_quantity"].text() or 0),
                    minimum_stock=float(fields["minimum_stock"].text() or 0),
                ))
                s.commit()
            self.load()
            QMessageBox.information(self, "Added", f"'{name}' added.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "Excel (*.xlsx);;CSV (*.csv)")
        if not path:
            return
        try:
            import pandas as pd
            df = pd.read_excel(path) if path.lower().endswith("xlsx") else pd.read_csv(path)
            required = {"name", "barcode", "sku", "purchase_price", "selling_price", "stock_quantity"}
            missing = required - set(df.columns)
            if missing:
                raise ValueError("Missing: " + ", ".join(missing))
            with SessionLocal() as s:
                for _, r in df.iterrows():
                    barcode = str(r.get("barcode", "")).strip()
                    sku = str(r.get("sku", "")).strip()
                    p = s.query(Product).filter((Product.barcode == barcode) | (Product.sku == sku)).first()
                    if p:
                        p.name = str(r["name"])
                        p.purchase_price = float(r["purchase_price"])
                        p.selling_price = float(r["selling_price"])
                        p.stock_quantity = float(r["stock_quantity"])
                        if "wholesale_price" in df.columns:
                            p.wholesale_price = float(r.get("wholesale_price", 0) or 0)
                        if "wholesale_min_qty" in df.columns:
                            p.wholesale_min_qty = float(r.get("wholesale_min_qty", 0) or 0)
                    else:
                        s.add(Product(
                            name=str(r["name"]), barcode=barcode, sku=sku,
                            purchase_price=float(r["purchase_price"]),
                            selling_price=float(r["selling_price"]),
                            wholesale_price=float(r.get("wholesale_price", 0) or 0),
                            wholesale_min_qty=float(r.get("wholesale_min_qty", 0) or 0),
                            stock_quantity=float(r["stock_quantity"])
                        ))
                s.commit()
            self.load()
            QMessageBox.information(self, "Import Complete", "Products imported.")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def export_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "products.csv", "CSV (*.csv)")
        if not path:
            return
        with SessionLocal() as s:
            ps = s.query(Product).all()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["name", "barcode", "sku", "purchase_price", "selling_price",
                        "wholesale_price", "wholesale_min_qty", "stock_quantity", "minimum_stock"])
            for p in ps:
                w.writerow([p.name, p.barcode, p.sku, p.purchase_price, p.selling_price,
                            p.wholesale_price, p.wholesale_min_qty, p.stock_quantity, p.minimum_stock])
        QMessageBox.information(self, "Export Complete", "Products exported.")


# =========================================================
# SALES WIDGET
# =========================================================
class SalesWidget(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(24, 22, 24, 22)
        l.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Sales History")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
        header.addWidget(title)
        header.addStretch()

        refresh = QPushButton("Refresh")
        refresh.setProperty("variant", "secondary")
        refresh.clicked.connect(self.load)
        header.addWidget(refresh)
        l.addLayout(header)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["INVOICE", "DATE", "CASHIER", "SUBTOTAL", "TOTAL", "PAYMENT", "PAID", "UDHAAR"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        l.addWidget(self.table, 1)
        self.load()

    def load(self):
        with SessionLocal() as s:
            rows = s.query(Sale, User).join(User, Sale.cashier_id == User.id).order_by(Sale.created_at.desc()).limit(1000).all()
        self.table.setRowCount(0)
        for sale, user in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 46)
            vals = [
                sale.invoice, sale.created_at.strftime("%d-%m-%Y %H:%M"),
                user.username, money(sale.subtotal), money(sale.total),
                sale.payment_method, money(sale.cash_received),
                money(sale.credit_amount) if sale.credit_amount > 0 else "—",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 7 and sale.credit_amount > 0:
                    item.setForeground(QColor("#D97706"))
                    fnt = item.font(); fnt.setBold(True); item.setFont(fnt)
                self.table.setItem(r, c, item)


# =========================================================
# INVENTORY WIDGET
# =========================================================
class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(24, 22, 24, 22)
        l.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Inventory")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
        header.addWidget(title)
        header.addStretch()

        refresh = QPushButton("Refresh")
        refresh.setProperty("variant", "secondary")
        refresh.clicked.connect(self.load)
        header.addWidget(refresh)
        l.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["PRODUCT", "STOCK", "MINIMUM", "STATUS", "PRICE"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        l.addWidget(self.table, 1)
        self.load()

    def load(self):
        with SessionLocal() as s:
            ps = s.query(Product).order_by(Product.stock_quantity).all()
        self.table.setRowCount(0)
        for p in ps:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 46)
            if p.stock_quantity <= 0:
                status, color = "OUT OF STOCK", "#DC2626"
            elif p.stock_quantity <= p.minimum_stock:
                status, color = "LOW", "#D97706"
            else:
                status, color = "OK", "#059669"
            vals = [p.name, f"{p.stock_quantity:.0f}", f"{p.minimum_stock:.0f}",
                    status, money(p.selling_price)]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 3:
                    item.setForeground(QColor(color))
                    fnt = item.font(); fnt.setBold(True); item.setFont(fnt)
                self.table.setItem(r, c, item)


# =========================================================
# CREDITS WIDGET
# =========================================================
class CreditsWidget(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(24, 22, 24, 22)
        l.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Udhaar / Credits")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
        header.addWidget(title)
        header.addStretch()

        new_cust = QPushButton("+ New Customer")
        new_cust.clicked.connect(self.new_customer)
        header.addWidget(new_cust)

        refresh = QPushButton("Refresh")
        refresh.setProperty("variant", "secondary")
        refresh.clicked.connect(self.load)
        header.addWidget(refresh)
        l.addLayout(header)

        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(14)
        l.addLayout(self.stats_layout)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or phone...")
        self.search.setFixedHeight(44)
        self.search.textChanged.connect(self.load)
        l.addWidget(self.search)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["NAME", "PHONE", "TOTAL CREDIT", "TOTAL PAID", "BALANCE", "ACTION"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        l.addWidget(self.table, 1)
        self.load()

    def load(self):
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        with SessionLocal() as s:
            all_cust = s.query(CreditCustomer).all()
            total_credit = sum(c.total_credit for c in all_cust)
            total_paid = sum(c.total_paid for c in all_cust)
            total_balance = sum(c.balance for c in all_cust)
            pending_count = sum(1 for c in all_cust if c.balance > 0)

        stats = [
            ("Total Credit Given", money(total_credit), "#4F46E5"),
            ("Total Received", money(total_paid), "#059669"),
            ("Outstanding Balance", money(total_balance), "#DC2626"),
            ("Pending Customers", str(pending_count), "#D97706"),
        ]
        for label, val, color in stats:
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(4)
            lbl = QLabel(label.upper())
            lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 800;")
            cl.addWidget(lbl)
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 900;")
            cl.addWidget(val_lbl)
            self.stats_layout.addWidget(card)

        q = self.search.text().strip()
        with SessionLocal() as s:
            query = s.query(CreditCustomer).order_by(CreditCustomer.balance.desc())
            if q:
                query = query.filter(
                    (CreditCustomer.name.ilike(f"%{q}%")) |
                    (CreditCustomer.phone.ilike(f"%{q}%"))
                )
            customers = query.all()

        self.table.setRowCount(0)
        for c in customers:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 56)
            vals = [c.name, c.phone, money(c.total_credit), money(c.total_paid), money(c.balance)]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if col == 4:
                    item.setForeground(QColor("#DC2626" if c.balance > 0 else "#059669"))
                    fnt = item.font(); fnt.setBold(True); item.setFont(fnt)
                self.table.setItem(r, col, item)

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 4, 4, 4); al.setSpacing(6)

            view = QPushButton("View")
            view.setProperty("variant", "secondary")
            view.setFixedHeight(36)
            view.clicked.connect(lambda _, cid=c.id: self.view_customer(cid))
            al.addWidget(view)

            pay = QPushButton("Receive")
            pay.setProperty("variant", "success")
            pay.setFixedHeight(36)
            pay.clicked.connect(lambda _, cid=c.id: self.receive_payment(cid))
            al.addWidget(pay)

            self.table.setCellWidget(r, 5, actions)

    def new_customer(self):
        d = QDialog(self)
        d.setWindowTitle("New Credit Customer")
        d.setFixedWidth(420)
        d.setStyleSheet(DIALOG_STYLE)
        v = QVBoxLayout(d)
        v.setContentsMargins(24, 24, 24, 24); v.setSpacing(12)

        t = QLabel("Add Credit Customer")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        v.addWidget(t)

        fields = {}
        for label in ["Name *", "Phone *", "Address", "Notes"]:
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
            v.addWidget(lbl)
            w = QLineEdit(); w.setFixedHeight(42)
            v.addWidget(w); fields[label] = w

        b = QPushButton("Save Customer"); b.setFixedHeight(46)
        b.clicked.connect(d.accept); v.addWidget(b)

        if d.exec() != QDialog.Accepted:
            return
        name = fields["Name *"].text().strip()
        phone = fields["Phone *"].text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Missing Info", "Name and phone required.")
            return

        with SessionLocal() as s:
            if s.query(CreditCustomer).filter_by(phone=phone).first():
                QMessageBox.warning(self, "Duplicate", "Customer with this phone exists.")
                return
            s.add(CreditCustomer(
                name=name, phone=phone,
                address=fields["Address"].text().strip(),
                notes=fields["Notes"].text().strip(),
            ))
            s.commit()
        self.load()

    def view_customer(self, cid):
        with SessionLocal() as s:
            c = s.get(CreditCustomer, cid)
            if not c:
                return
            transactions = s.query(CreditTransaction).filter_by(customer_id=cid).order_by(CreditTransaction.created_at.desc()).all()

            d = QDialog(self)
            d.setWindowTitle(f"Customer — {c.name}")
            d.setFixedSize(620, 600)
            d.setStyleSheet(DIALOG_STYLE)

            v = QVBoxLayout(d)
            v.setContentsMargins(24, 24, 24, 24); v.setSpacing(12)

            name = QLabel(c.name)
            name.setStyleSheet("font-size: 22px; font-weight: 900; color: #0F172A;")
            v.addWidget(name)

            info = QLabel(f"📞 {c.phone}    📍 {c.address or 'No address'}")
            info.setStyleSheet("color: #64748B; font-size: 13px;")
            v.addWidget(info)

            boxes = QHBoxLayout()
            for label, val, bg, fg in [
                ("TOTAL CREDIT", money(c.total_credit), "#FEF3C7", "#92400E"),
                ("TOTAL PAID", money(c.total_paid), "#ECFDF5", "#047857"),
                ("BALANCE", money(c.balance), "#FEE2E2", "#991B1B"),
            ]:
                box = QFrame()
                box.setStyleSheet(f"background: {bg}; border-radius: 10px;")
                bl = QVBoxLayout(box)
                bl.setContentsMargins(14, 12, 14, 12); bl.setSpacing(3)
                bl.addWidget(QLabel(f"<span style='color:{fg};font-size:10px;font-weight:800;'>{label}</span>"))
                vl = QLabel(val)
                vl.setStyleSheet(f"color: {fg}; font-size: 18px; font-weight: 900;")
                bl.addWidget(vl)
                boxes.addWidget(box)
            v.addLayout(boxes)

            table = QTableWidget(0, 4)
            table.setHorizontalHeaderLabels(["DATE", "TYPE", "AMOUNT", "BALANCE"])
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setVisible(False)
            table.setShowGrid(False)

            for t in transactions:
                r = table.rowCount()
                table.insertRow(r); table.setRowHeight(r, 44)
                vals = [t.created_at.strftime("%d-%m-%Y %H:%M"),
                        "Udhaar" if t.type == "credit" else "Payment",
                        money(t.amount), money(t.balance_after)]
                for col, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    if col == 1:
                        item.setForeground(QColor("#DC2626" if t.type == "credit" else "#059669"))
                    table.setItem(r, col, item)

            v.addWidget(table, 1)

            close = QPushButton("Close"); close.setFixedHeight(46)
            close.clicked.connect(d.accept); v.addWidget(close)
            d.exec()

    def receive_payment(self, cid):
        with SessionLocal() as s:
            c = s.get(CreditCustomer, cid)
            if not c:
                return
            name, phone, balance = c.name, c.phone, c.balance

        if balance <= 0:
            QMessageBox.information(self, "No Balance", f"{name} has no outstanding balance.")
            return

        d = QDialog(self)
        d.setWindowTitle(f"Receive Payment")
        d.setFixedWidth(440)
        d.setStyleSheet(DIALOG_STYLE)
        v = QVBoxLayout(d)
        v.setContentsMargins(24, 24, 24, 24); v.setSpacing(12)

        t = QLabel("Receive Payment")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        v.addWidget(t)
        v.addWidget(QLabel(f"{name} • {phone}"))

        box = QFrame()
        box.setStyleSheet("background: #FEF3C7; border-radius: 10px;")
        bl = QVBoxLayout(box); bl.setContentsMargins(16, 12, 16, 12)
        bl.addWidget(QLabel("<span style='color:#92400E;font-size:11px;font-weight:800;'>OUTSTANDING BALANCE</span>"))
        vl = QLabel(money(balance))
        vl.setStyleSheet("color: #92400E; font-size: 22px; font-weight: 900;")
        bl.addWidget(vl)
        v.addWidget(box)

        v.addWidget(QLabel("PAYMENT AMOUNT"))
        amount = QDoubleSpinBox()
        amount.setMaximum(999999999); amount.setDecimals(2); amount.setValue(balance)
        amount.setFixedHeight(46); amount.setStyleSheet("font-size: 16px; font-weight: 700;")
        v.addWidget(amount)

        v.addWidget(QLabel("NOTE (optional)"))
        note = QLineEdit(); note.setPlaceholderText("e.g., Cash received"); note.setFixedHeight(42)
        v.addWidget(note)

        b = QPushButton("Receive Payment"); b.setFixedHeight(50)
        b.clicked.connect(d.accept); v.addWidget(b)

        if d.exec() != QDialog.Accepted:
            return
        pay_amt = amount.value()
        if pay_amt <= 0:
            QMessageBox.warning(self, "Invalid", "Amount must be > 0.")
            return

        with SessionLocal() as s:
            c = s.get(CreditCustomer, cid)
            c.total_paid += pay_amt
            c.balance = max(0, c.total_credit - c.total_paid)
            s.add(CreditTransaction(
                customer_id=cid, type="payment", amount=pay_amt,
                description=note.text().strip() or "Payment received",
                balance_after=c.balance,
            ))
            new_bal = c.balance
            s.commit()

        QMessageBox.information(self, "Payment Received",
                                f"Recorded {money(pay_amt)}.\n\nNew Balance: {money(new_bal)}")
        self.load()


# =========================================================
# DASHBOARD (PROFESSIONAL with CHARTS)
# =========================================================
class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #F1F5F9; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.scroll)

        self.container = QWidget()
        self.container.setStyleSheet("background: #F1F5F9;")
        self.scroll.setWidget(self.container)

        self.l = QVBoxLayout(self.container)
        self.l.setContentsMargins(28, 26, 28, 26)
        self.l.setSpacing(20)

        self.refresh()

    def refresh(self):
        while self.l.count():
            item = self.l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear(item.layout())

        # ===== HEADER =====
        header = QHBoxLayout()
        title_box = QVBoxLayout(); title_box.setSpacing(2)
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A; letter-spacing: -0.5px;")
        title_box.addWidget(title)
        sub = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        sub.setStyleSheet("color: #64748B; font-size: 13px;")
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setProperty("variant", "secondary")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        self.l.addLayout(header)

        # ===== DATA =====
        with SessionLocal() as s:
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())

            today_sales = s.query(Sale).filter(Sale.created_at >= today_start).all()
            week_start = today_start - timedelta(days=today.weekday())
            week_sales = s.query(Sale).filter(Sale.created_at >= week_start).all()

            total_products = s.query(Product).count()
            low_stock = s.query(Product).filter(
                Product.stock_quantity <= Product.minimum_stock,
                Product.stock_quantity > 0
            ).count()
            out_of_stock = s.query(Product).filter(Product.stock_quantity <= 0).count()

            credit_customers = s.query(CreditCustomer).all()
            total_udhaar = sum(c.balance for c in credit_customers)
            pending_customers = sum(1 for c in credit_customers if c.balance > 0)

            # Last 7 days sales
            last_7_days = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                d_start = datetime.combine(d, datetime.min.time())
                d_end = d_start + timedelta(days=1)
                day_sales = s.query(Sale).filter(
                    Sale.created_at >= d_start,
                    Sale.created_at < d_end
                ).all()
                last_7_days.append((d.strftime("%a"), sum(x.total for x in day_sales)))

            # Top products (last 30 days)
            from sqlalchemy import func
            month_start = today_start - timedelta(days=30)
            top_products_query = s.query(
                SaleItem.product_name,
                func.sum(SaleItem.subtotal).label("total")
            ).join(Sale, SaleItem.sale_id == Sale.id).filter(
                Sale.created_at >= month_start
            ).group_by(SaleItem.product_name).order_by(func.sum(SaleItem.subtotal).desc()).limit(6).all()
            top_products = [(name[:18], float(total)) for name, total in top_products_query]

            # Category distribution
            cat_dist = s.query(
                Category.name,
                func.count(Product.id)
            ).join(Product, Product.category_id == Category.id).group_by(Category.name).all()
            cat_data = [(name, count) for name, count in cat_dist]

        # ===== STAT CARDS =====
        grid = QGridLayout()
        grid.setSpacing(16)

        stats = [
            ("Today's Sales", money(sum(x.total for x in today_sales)),
             "💰", "#4F46E5", f"{len(today_sales)} transactions"),
            ("This Week", money(sum(x.total for x in week_sales)),
             "📈", "#059669", f"{len(week_sales)} transactions"),
            ("Total Products", str(total_products),
             "📦", "#D97706", f"{low_stock} low • {out_of_stock} out"),
            ("Udhaar Balance", money(total_udhaar),
             "💳", "#DC2626", f"{pending_customers} pending"),
        ]
        for i, (t, v, ic, c, sub) in enumerate(stats):
            card = StatCard(t, v, ic, c, sub)
            card.setMinimumHeight(140)
            grid.addWidget(card, 0, i)
        self.l.addLayout(grid)

        # ===== CHARTS ROW =====
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Bar chart: Last 7 days
        bar_card = self._make_chart_card(
            "📊  Sales — Last 7 Days",
            "Daily revenue breakdown"
        )
        bar_chart = BarChartWidget(last_7_days)
        bar_chart.setMinimumHeight(280)
        bar_card.layout().addWidget(bar_chart)
        charts_row.addWidget(bar_card, 3)

        # Donut chart: Categories
        donut_card = self._make_chart_card(
            "🍩  Products by Category",
            "Category-wise product count"
        )
        donut_chart = DonutChartWidget(cat_data)
        donut_chart.setMinimumHeight(280)
        donut_card.layout().addWidget(donut_chart)
        charts_row.addWidget(donut_card, 2)

        self.l.addLayout(charts_row)

        # ===== BOTTOM ROW: Recent Sales + Top Products + Alerts =====
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # Recent Transactions
        recent_card = self._make_chart_card("🕐  Recent Transactions", "Latest 5 sales")
        with SessionLocal() as s:
            recent = s.query(Sale).order_by(Sale.created_at.desc()).limit(5).all()
            recent_data = [(r.invoice, r.created_at, r.total, r.payment_method) for r in recent]

        if not recent_data:
            empty = QLabel("No transactions yet")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 30px;")
            recent_card.layout().addWidget(empty)
        else:
            for inv, dt, total, method in recent_data:
                row = QFrame()
                row.setStyleSheet("background: #F8FAFC; border-radius: 8px;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 10, 12, 10); rl.setSpacing(8)

                inv_lbl = QLabel(inv.replace("INV-", "#")[:12])
                inv_lbl.setStyleSheet("color: #4F46E5; font-size: 12px; font-weight: 800;")
                inv_lbl.setFixedWidth(90)
                rl.addWidget(inv_lbl)

                time_lbl = QLabel(dt.strftime("%I:%M %p"))
                time_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
                rl.addWidget(time_lbl)
                rl.addStretch()

                amt_lbl = QLabel(money(total))
                amt_lbl.setStyleSheet("color: #0F172A; font-size: 13px; font-weight: 800;")
                rl.addWidget(amt_lbl)

                recent_card.layout().addWidget(row)

        recent_card.layout().addStretch()
        bottom.addWidget(recent_card, 1)

        # Top Products
        top_card = self._make_chart_card("🏆  Top Selling Products", "Last 30 days revenue")
        if not top_products:
            empty = QLabel("No sales data yet")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 12px; padding: 30px;")
            top_card.layout().addWidget(empty)
        else:
            for i, (name, total) in enumerate(top_products):
                row = QFrame()
                row.setStyleSheet("background: #F8FAFC; border-radius: 8px;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 10, 12, 10); rl.setSpacing(8)

                rank = QLabel(f"#{i+1}")
                rank.setStyleSheet("""
                    background: #4F46E5; color: white;
                    border-radius: 10px; padding: 2px 8px;
                    font-size: 11px; font-weight: 800;
                """)
                rank.setFixedWidth(36)
                rank.setAlignment(Qt.AlignCenter)
                rl.addWidget(rank)

                name_lbl = QLabel(name)
                name_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 700;")
                rl.addWidget(name_lbl, 1)

                amt_lbl = QLabel(money(total))
                amt_lbl.setStyleSheet("color: #059669; font-size: 13px; font-weight: 800;")
                rl.addWidget(amt_lbl)

                top_card.layout().addWidget(row)
        top_card.layout().addStretch()
        bottom.addWidget(top_card, 1)

        # Alerts
        alert_card = self._make_chart_card("⚠️  Stock Alerts", "Low & out of stock")
        with SessionLocal() as s:
            low_items = s.query(Product).filter(
                Product.stock_quantity <= Product.minimum_stock,
                Product.stock_quantity > 0
            ).order_by(Product.stock_quantity).limit(4).all()
            out_items = s.query(Product).filter(
                Product.stock_quantity <= 0
            ).limit(4).all()

        alerts = [(p.name, p.stock_quantity, True) for p in out_items] + \
                 [(p.name, p.stock_quantity, False) for p in low_items]

        if not alerts:
            ok = QLabel("✓ All products well stocked")
            ok.setAlignment(Qt.AlignCenter)
            ok.setStyleSheet("color: #059669; font-size: 12px; padding: 30px; font-weight: 600;")
            alert_card.layout().addWidget(ok)
        else:
            for name, stock, is_out in alerts[:6]:
                row = QFrame()
                bg = "#FEE2E2" if is_out else "#FEF3C7"
                row.setStyleSheet(f"background: {bg}; border-radius: 8px;")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 10, 12, 10); rl.setSpacing(8)

                name_lbl = QLabel(name[:20])
                name_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 700;")
                rl.addWidget(name_lbl, 1)

                stock_lbl = QLabel("OUT" if is_out else f"{stock:.0f} left")
                stock_lbl.setStyleSheet(f"""
                    color: {'#DC2626' if is_out else '#D97706'};
                    font-size: 11px; font-weight: 800;
                """)
                rl.addWidget(stock_lbl)

                alert_card.layout().addWidget(row)
        alert_card.layout().addStretch()
        bottom.addWidget(alert_card, 1)

        self.l.addLayout(bottom)
        self.l.addStretch()

    def _make_chart_card(self, title, subtitle):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border: 1px solid #E8ECF1;
                border-radius: 14px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F172A; background: transparent;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #64748B; font-size: 11px; background: transparent;")
        layout.addWidget(sub_lbl)

        return card

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear(item.layout())


# =========================================================
# MAIN WINDOW (with role-based permissions)
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        login = LoginDialog()
        if login.exec() != QDialog.Accepted:
            raise SystemExit
        self.user = login.user
        self.role = self.user[2]

        self.setWindowTitle(f"Retail POS — {self.user[1]} ({self.role})")
        self.resize(1460, 900)
        self.setMinimumSize(1200, 720)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ============ TOP BAR ============
        top = QFrame()
        top.setObjectName("TopBar")
        top.setStyleSheet(TOPBAR_STYLE)
        top.setFixedHeight(68)

        tl = QHBoxLayout(top)
        tl.setContentsMargins(20, 12, 20, 12)
        tl.setSpacing(12)

        self.search = LiveSearchBar()
        self.search.product_selected.connect(self._on_product_selected)
        self.search.setStyleSheet(TOPBAR_STYLE.replace("QLineEdit#SearchBar", "LiveSearchBar"))
        # Only allow search if POS accessible
        if not has_permission(self.role, "pos"):
            self.search.setDisabled(True)
            self.search.setPlaceholderText("Search disabled for your role")
        tl.addWidget(self.search, 1)

        notif = QPushButton("🔔")
        notif.setObjectName("IconBtn")
        notif.setStyleSheet(TOPBAR_STYLE)
        notif.setCursor(Qt.PointingHandCursor)
        tl.addWidget(notif)

        avatar = QLabel(self.user[1][0].upper())
        avatar.setObjectName("UserAvatar")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet(SIDEBAR_STYLE)
        tl.addWidget(avatar)

        root.addWidget(top)

        # ============ BODY ============
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        side = QFrame()
        side.setObjectName("Sidebar")
        side.setStyleSheet(SIDEBAR_STYLE)
        side.setFixedWidth(230)

        sl = QVBoxLayout(side)
        sl.setContentsMargins(16, 20, 16, 20)
        sl.setSpacing(6)

        brand = QLabel("RETAIL POS")
        brand.setObjectName("BrandLogo")
        brand.setStyleSheet(SIDEBAR_STYLE)
        sl.addWidget(brand)

        tag = QLabel("POINT OF SALE")
        tag.setObjectName("BrandTag")
        tag.setStyleSheet(SIDEBAR_STYLE)
        sl.addWidget(tag)

        sl.addSpacing(20)

        # User card
        user_card = QFrame()
        user_card.setObjectName("UserCard")
        user_card.setStyleSheet(SIDEBAR_STYLE)
        uc = QHBoxLayout(user_card)
        uc.setContentsMargins(12, 10, 12, 10)
        uc.setSpacing(10)

        u_avatar = QLabel(self.user[1][0].upper())
        u_avatar.setObjectName("UserAvatar")
        u_avatar.setAlignment(Qt.AlignCenter)
        u_avatar.setFixedSize(36, 36)
        u_avatar.setStyleSheet(SIDEBAR_STYLE)
        uc.addWidget(u_avatar)

        u_info = QVBoxLayout()
        u_info.setSpacing(1)
        u_name = QLabel(self.user[1])
        u_name.setObjectName("UserName")
        u_name.setStyleSheet(SIDEBAR_STYLE)
        u_role = QLabel(self.role)
        u_role.setObjectName("UserRole")
        u_role.setStyleSheet(SIDEBAR_STYLE)
        u_info.addWidget(u_name)
        u_info.addWidget(u_role)
        uc.addLayout(u_info)
        uc.addStretch()

        sl.addWidget(user_card)
        sl.addSpacing(20)

        nav_label = QLabel("MENU")
        nav_label.setObjectName("SectionLabel")
        nav_label.setStyleSheet(SIDEBAR_STYLE)
        sl.addWidget(nav_label)

        self.stack = QStackedWidget()

        # Instantiate pages (will be filtered by role)
        self.dashboard = DashboardWidget() if has_permission(self.role, "dashboard") else None
        self.pos = POSWidget(self.user, self.dashboard.refresh if self.dashboard else None) if has_permission(self.role, "pos") else None
        self.products = ProductsWidget() if has_permission(self.role, "products") else None
        self.inventory = InventoryWidget() if has_permission(self.role, "inventory") else None
        self.sales = SalesWidget() if has_permission(self.role, "sales") else None
        self.credits = CreditsWidget() if has_permission(self.role, "credits") else None
        self.users = UsersWidget() if has_permission(self.role, "users") else None

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        pages_config = [
            ("dashboard", "🏠   Dashboard", self.dashboard),
            ("pos", "🛒   POS", self.pos),
            ("products", "📦   Products", self.products),
            ("inventory", "📊   Inventory", self.inventory),
            ("sales", "🧾   Sales", self.sales),
            ("credits", "💳   Udhaar / Credits", self.credits),
            ("users", "👥   Users", self.users),
        ]

        first_btn = None
        for key, name, page in pages_config:
            if page is None:
                continue
            b = QPushButton(name)
            b.setObjectName("NavButton")
            b.setStyleSheet(SIDEBAR_STYLE)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(44)
            b.clicked.connect(lambda _, p=page: self.show_page(p))
            self.nav_group.addButton(b)
            sl.addWidget(b)
            self.stack.addWidget(page)
            if first_btn is None:
                first_btn = b

        # Default page
        if first_btn:
            first_btn.setChecked(True)
            if self.pos is not None:
                self.stack.setCurrentWidget(self.pos)
            elif self.dashboard is not None:
                self.stack.setCurrentWidget(self.dashboard)
            elif self.credits is not None:
                self.stack.setCurrentWidget(self.credits)

        sl.addStretch()

        bottom_label = QLabel("ACTIONS")
        bottom_label.setObjectName("SectionLabel")
        bottom_label.setStyleSheet(SIDEBAR_STYLE)
        sl.addWidget(bottom_label)

        if has_permission(self.role, "backup"):
            backup = QPushButton("💾   Backup")
            backup.setObjectName("NavButton")
            backup.setStyleSheet(SIDEBAR_STYLE)
            backup.setFixedHeight(44)
            backup.setCursor(Qt.PointingHandCursor)
            backup.clicked.connect(self.backup)
            sl.addWidget(backup)

        logout = QPushButton("🚪   Logout")
        logout.setObjectName("NavButton")
        logout.setStyleSheet(SIDEBAR_STYLE)
        logout.setFixedHeight(44)
        logout.setCursor(Qt.PointingHandCursor)
        logout.clicked.connect(self.close)
        sl.addWidget(logout)

        body.addWidget(side)
        body.addWidget(self.stack, 1)

        self.setStyleSheet(GLOBAL_STYLE)

    def show_page(self, p):
        self.stack.setCurrentWidget(p)
        if hasattr(p, "load"):
            p.load()
        if p is self.dashboard and p is not None:
            p.refresh()

    def _on_product_selected(self, pid):
        if self.pos is None:
            QMessageBox.warning(self, "Access Denied",
                                "You don't have permission to use POS.")
            return
        self.stack.setCurrentWidget(self.pos)
        # Check the POS nav button
        for btn in self.nav_group.buttons():
            if "POS" in btn.text():
                btn.setChecked(True)
                break
        self.pos.add_product(pid)

    def backup(self):
        from app.database import DB_PATH, BACKUP_DIR
        name = BACKUP_DIR / f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        try:
            shutil.copy2(DB_PATH, name)
            QMessageBox.information(self, "Backup Complete", f"Saved to:\n{name}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))