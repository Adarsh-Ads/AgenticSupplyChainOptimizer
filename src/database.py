import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

def initialize_db(csv_input):
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    
    # Load data
    df = pd.read_csv(csv_input)
    print("✅ CSV Loaded. Mapping columns...")

    # 1. MAPPING YOUR SPECIFIC COLUMNS
    column_mapping = {
        'Product ID': 'product_id',
        'Inventory Level': 'current_stock',
        'Price': 'unit_price',
        'Date': 'date',
        'Units Sold': 'units_sold'
    }
    
    df = df.rename(columns=column_mapping)

    # 2. ADDING MISSING DATA (Product Name)
    # Since your CSV doesn't have names, we'll create a generic one like "Product-ID-123"
    if 'product_name' not in df.columns:
        df['product_name'] = "Product-" + df['product_id'].astype(str)

    # 3. CREATE PRODUCTS TABLE
    # We take the most recent record for each product to get its current stock
    products = df[['product_id', 'product_name', 'current_stock', 'unit_price']].drop_duplicates('product_id', keep='last')
    products.to_sql('products', conn, if_exists='replace', index=False)

    # 4. CREATE SALES HISTORY TABLE
    sales = df[['product_id', 'date', 'units_sold']]
    sales.to_sql('sales_history', conn, if_exists='replace', index=False)
    
    # 5. CREATE SUPPLIERS TABLE
    conn.execute("DROP TABLE IF EXISTS suppliers")
    conn.execute('''
        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    ''')
    conn.execute("INSERT INTO suppliers VALUES (1, 'Global Inventory Corp', 'orders@global-inv.com')")
    
    conn.commit()
    conn.close()
    print(f"✅ Success! SQL Database built at {DB_PATH}")

if __name__ == "__main__":
    initialize_db('data/retail_data.csv')