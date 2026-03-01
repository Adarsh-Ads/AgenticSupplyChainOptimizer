from fastapi import FastAPI
import sqlite3
import os
from engine import forecast_stock_risk

app = FastAPI(title="Agentic Supply Chain Dashboard")
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

@app.get("/")
def home():
    return {"status": "Online", "message": "Supply Chain Optimizer is Running"}

@app.get("/inventory")
def get_inventory():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    items = cursor.execute("SELECT * FROM products").fetchall()
    conn.close()
    return [dict(row) for row in items]

@app.post("/trigger/{product_id}")
def trigger_agent(product_id: str):
    # This calls your engine.py logic
    forecast_stock_risk(product_id)
    return {"message": f"Agent triggered for product {product_id}"}