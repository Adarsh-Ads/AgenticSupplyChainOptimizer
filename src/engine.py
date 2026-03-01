import os
import sqlite3
import pandas as pd
import xgboost as xgb
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agent_tools import get_supplier_details, update_inventory_status  


load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")


# UPDATED: The Intelligent Agent for Agno 1.0+
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[get_supplier_details, update_inventory_status],
    description="You are a Supply Chain Manager.",
    instructions=[
        "1. Identify the product ID and name from the input.",
        "2. Call get_supplier_details to find the supplier email.",
        "3. Draft a professional restock email.",
        "4. Call update_inventory_status to log the draft creation."
    ],
    markdown=True,
)

def forecast_stock_risk(product_id):
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}. Run database.py first!")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Fetch sales history
    query = f"SELECT units_sold FROM sales_history WHERE product_id='{product_id}'"
    df = pd.read_sql(query, conn)
    
    if len(df) < 5:
        print(f"ℹ️ Insufficient data for Product {product_id} to forecast.")
        return

    # XGBoost Forecasting (Predicting burn rate)
    df['lag_1'] = df['units_sold'].shift(1)
    train_df = df.dropna()
    
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=50)
    model.fit(train_df[['lag_1']], train_df['units_sold'])

    last_sale = df['units_sold'].iloc[-1].reshape(-1, 1)
    predicted_daily_sales = model.predict(pd.DataFrame(last_sale, columns=['lag_1']))[0]
    
    # Get current stock levels
    stock_info = conn.execute(
        f"SELECT current_stock, product_name FROM products WHERE product_id='{product_id}'"
    ).fetchone()
    
    current_stock, product_name = stock_info[0], stock_info[1]
    days_left = current_stock / max(predicted_daily_sales, 0.1)

    # Agentic Trigger
    if days_left < 10: # Alerting if less than 10 days left
        print(f"⚠️ ALERT: {product_name} running low ({days_left:.1f} days left).")
        
        prompt = f"""
        INVENTORY ALERT:
        Product: {product_name}
        Stock Level: {current_stock}
        Predicted Daily Sales: {predicted_daily_sales:.2f}
        Days until empty: {days_left:.1f}
        
        Task: Draft a professional restock email to 'Global Inventory Corp'. 
        Mention the data-driven forecast and request a quote for 500 units.
        """
        agent.print_response(prompt)
    else:
        print(f"✅ {product_name} stock is stable. Estimated {days_left:.1f} days remaining.")

    conn.close()

if __name__ == "__main__":
    # Connect to find a product that actually has data
    conn = sqlite3.connect(DB_PATH)
    
    # Query to find products with at least 5 rows of sales history
    valid_products = pd.read_sql("""
        SELECT product_id, COUNT(*) as record_count 
        FROM sales_history 
        GROUP BY product_id 
        HAVING record_count >= 5 
        ORDER BY record_count DESC 
        LIMIT 1
    """, conn)
    
    conn.close()

    if not valid_products.empty:
        best_id = valid_products['product_id'].iloc[0]
        records = valid_products['record_count'].iloc[0]
        print(f"📈 Found Product {best_id} with {records} data points. Running forecast...")
        forecast_stock_risk(best_id)
    else:
        print("❌ No products found with enough history (min 5 rows).")
        print("💡 Suggestion: Check your CSV to see if products have multiple dates of sales.")