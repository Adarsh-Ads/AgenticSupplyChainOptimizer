import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Supply Chain AI", layout="wide")

# --- SIDEBAR STATUS ---
st.sidebar.title("🛠️ System Control")
api_url = "http://127.0.0.1:8000"

# Check if Backend is alive
backend_online = False
try:
    health_check = requests.get(f"{api_url}/", timeout=2)
    if health_check.status_code == 200:
        st.sidebar.success("✅ Backend: Connected")
        backend_online = True
except:
    st.sidebar.error("❌ Backend: Offline")
    st.sidebar.info("Run: uvicorn main:app --reload --app-dir src")

st.title("📦 Agentic Supply Chain Optimizer")

# --- MAIN CONTENT ---
if not backend_online:
    st.warning("Please start the FastAPI server in your terminal to see data.")
    st.image("https://error404.fun/img/illustrations/02.png", width=400) # Fun placeholder
else:
    try:
        # Fetch Inventory
        response = requests.get(f"{api_url}/inventory")
        data = response.json()
        
        if data:
            df = pd.DataFrame(data)
            
            # Metrics
            m1, m2 = st.columns(2)
            m1.metric("Items in Catalog", len(df))
            m2.metric("Stock Alerts", len(df[df['current_stock'] < 100]))

            st.divider()
            st.subheader("Inventory Status")
            st.dataframe(df, use_container_width=True)

            # Agent Trigger
            st.sidebar.divider()
            st.sidebar.subheader("🤖 AI Agent")
            target_id = st.sidebar.selectbox("Select Product ID", df['product_id'].unique())
            
            if st.sidebar.button("Run AI Forecast"):
                with st.spinner("Groq is thinking..."):
                    res = requests.post(f"{api_url}/trigger/{target_id}")
                    st.sidebar.write(res.json().get("message"))
                    st.toast("Check Terminal for Email Draft!")
        else:
            st.info("Database is connected but empty. Run database.py first.")

    except Exception as e:
        st.error(f"Error fetching data: {e}")