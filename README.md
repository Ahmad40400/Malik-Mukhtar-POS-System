# Offline POS System

A local/offline Pakistani retail POS built with Python + PySide6 + SQLite.

## Run
```bash
pip install -r requirements.txt
python main.py
```

First launch creates the database and setup defaults.

Default development login:
- Username: admin
- Password: admin123

Change the password before real use.

## Features
- Offline SQLite database
- Admin/Cashier roles
- Product catalog
- Barcode/SKU/name search
- POS cart
- Cash/card/bank/other payments
- Hold/resume sales
- Thermal receipt preview/printing
- Sales history
- Inventory and stock movements
- Customers
- CSV/XLSX product import/export
- Reports
- Backup/restore
- PKR currency

## Windows EXE
```bash
pip install pyinstaller
pyinstaller --windowed --name POS_System main.py
```
