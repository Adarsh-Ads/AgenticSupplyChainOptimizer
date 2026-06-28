import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

def initialize_db(csv_input):
    """
    Data Ingestion Pipeline: Ingests unstructured source data files, applies structural
    schema definitions, handles window drops, and constructs indexing constraints in the SQLite targets.
    """
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(csv_input)
    print("✅ CSV Loaded. Mapping columns...")

    column_mapping = {
        'Product ID': 'product_id',
        'Inventory Level': 'current_stock',
        'Price': 'unit_price',
        'Date': 'date',
        'Units Sold': 'units_sold'
    }
    df = df.rename(columns=column_mapping)

    if 'product_name' not in df.columns:
        df['product_name'] = "Product-" + df['product_id'].astype(str)

    # Dedup windowing step: Extracts the latest current tracking state metrics for the inventory system
    products = df[['product_id', 'product_name', 'current_stock', 'unit_price']].drop_duplicates('product_id', keep='last')
    products.to_sql('products', conn, if_exists='replace', index=False)

    sales = df[['product_id', 'date', 'units_sold']]
    sales.to_sql('sales_history', conn, if_exists='replace', index=False)
    
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