import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

def get_supplier_details(product_id: str):
    """Fetches the supplier name and email for a given product ID from the SQL database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We join the products and suppliers tables
    query = """
        SELECT s.name, s.email 
        FROM suppliers s 
        JOIN products p ON p.product_id = ?
        LIMIT 1
    """
    result = cursor.execute(query, (product_id,)).fetchone()
    conn.close()
    
    if result:
        return {"supplier_name": result[0], "supplier_email": result[1]}
    return "Supplier not found."

def update_inventory_status(product_id: str, status: str):
    """Logs the agent's action in a text file for the dashboard to read."""
    with open("data/agent_log.txt", "a") as f:
        f.write(f"Product {product_id}: {status}\n")
    return f"Logged status: {status}"