# bulk_wholesale_setup.py
"""
Bulk set wholesale prices for all products
Retail price ka 10% kam wholesale price set karta hai
Default wholesale_min_qty = 6 (6 ya zyada par wholesale lagegi)
"""

from app.database import SessionLocal, init_db
from app.models import Product

# ============ SETTINGS - YEH CHANGE KAR SAKTE HAIN ============
DEFAULT_WHOLESALE_DISCOUNT = 10    # Wholesale price = Retail - 10%
DEFAULT_MIN_QTY = 6                # 6 ya zyada par wholesale lagegi
# ==============================================================

def bulk_setup():
    init_db()
    
    with SessionLocal() as s:
        products = s.query(Product).all()
        
        if not products:
            print("❌ Koi product nahi mila database mein.")
            return
        
        print(f"📦 Total products: {len(products)}")
        print(f"⚙️  Settings: Wholesale = Retail - {DEFAULT_WHOLESALE_DISCOUNT}%")
        print(f"⚙️  Min Qty for wholesale: {DEFAULT_MIN_QTY}")
        print()
        
        updated = 0
        skipped = 0
        
        for p in products:
            # Sirf unko update karein jinme wholesale set nahi hai
            if p.wholesale_price == 0 or p.wholesale_price is None:
                # Wholesale price calculate karein
                discount = p.selling_price * (DEFAULT_WHOLESALE_DISCOUNT / 100)
                wholesale = p.selling_price - discount
                
                # Round to nearest 5 rupees (professional look)
                wholesale = round(wholesale / 5) * 5
                
                p.wholesale_price = wholesale
                p.wholesale_min_qty = DEFAULT_MIN_QTY
                updated += 1
                
                print(f"✅ {p.name[:40]:40} | Retail: Rs. {p.selling_price:6.0f} | Wholesale: Rs. {wholesale:6.0f}")
            else:
                skipped += 1
        
        s.commit()
        
        print()
        print("=" * 70)
        print(f"🎉 COMPLETE!")
        print(f"   ✅ Updated: {updated} products")
        print(f"   ⏭️  Skipped: {skipped} products (already had wholesale price)")
        print("=" * 70)
        print()
        print("▶️  Ab POS khol kar test karein:")
        print("   1. POS page par jaayein")
        print("   2. Kisi bhi product ko cart mein add karein")
        print("   3. Qty barha kar 6 ya zyada karein")
        print("   4. Wholesale price automatically lagegi ✅")


if __name__ == "__main__":
    bulk_setup()