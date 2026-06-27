from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os
from dotenv import load_dotenv
from src.engine import forecast_stock_risk

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

app = FastAPI(title="Agentic SCM API Gateway")

class AnalysisPayload(BaseModel):
    est_days_left: float
    target_days: float

@app.get("/inventory")
def get_inventory():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database missing. Initialize database.py first.")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        rows = cursor.execute("SELECT * FROM products").fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/trigger/{product_id}")
def trigger_analysis(product_id: str, payload: AnalysisPayload):
    try:
        result = forecast_stock_risk(
            product_id=product_id, 
            est_days_left=payload.est_days_left, 
            target_days=payload.target_days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))