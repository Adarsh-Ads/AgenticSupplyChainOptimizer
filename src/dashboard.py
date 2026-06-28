import sys
import os
import re

# Dynamic runtime modification of system path to correctly resolve sibling dependencies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SCM AI Optimizer", layout="wide")
API_URL = "http://127.0.0.1:8000"

st.title("📦 Agentic Supply Chain Control Tower")

try:
    # Synchronous I/O REST request fetching structured states from the FastAPI web service
    inventory_res = requests.get(f"{API_URL}/inventory")
    inventory_res.raise_for_status()
    df = pd.DataFrame(inventory_res.json())
    
    # Deriving critical time-series runway vectors based on daily consumption metrics
    df['est_days_left'] = df['current_stock'] / 50 

    col_table, col_actions = st.columns([1.3, 1])

    with col_table:
        st.subheader("📊 Live Inventory Status")
        
        # Color Mapping Heuristics Engine: Dynamic CSS injections based on structural threshold invariants
        def apply_row_styles(row):
            if row['current_stock'] <= 0:
                return ['background-color: #721c24; color: #f8d7da; font-weight: bold'] * len(row)  # Out of Stock (Critical Red)
            if row['est_days_left'] <= 5:
                return ['background-color: #856404; color: #fff3cd; font-weight: bold'] * len(row)  # Low Runway (Warning Yellow)
            return ['background-color: #155724; color: #d4edda'] * len(row)                        # Healthy Stock (Stable Green)

        # Compliant table loading utilizing layout width configuration strings
        st.dataframe(df.style.apply(apply_row_styles, axis=1), width="stretch", height=500)

    with col_actions:
        st.subheader("🎯 Action Center")
        with st.container(border=True):
            target_id = st.selectbox("Select Product", df['product_id'].unique())
            target_days = st.slider("Target Buffer (Days)", 7, 90, 30)
            
            if st.button("🚀 Run AI Analysis", width="stretch", type="primary"):
                days_val = float(df.loc[df['product_id'] == target_id, 'est_days_left'].values[0])
                payload = {"est_days_left": days_val, "target_days": float(target_days)}
                
                res = requests.post(f"{API_URL}/trigger/{target_id}", json=payload).json()
                raw_text = res.get("analysis", "").strip()
                
                # --- TOKENS BOUNDARY REGEX EXTRACTION ENGINE ---
                # Employs non-consuming lookahead assertions to block hidden LLM metadata text leakages
                try:
                    analysis_match = re.search(r"START_ANALYSIS\s*(.*?)(?=START_EMAIL|END_OUTPUT|END_ANALYSIS|$)", raw_text, re.DOTALL | re.IGNORECASE)
                    email_match = re.search(r"START_EMAIL\s*(.*?)(?=END_OUTPUT|END_EMAIL|START_SCHEMA|$)", raw_text, re.DOTALL | re.IGNORECASE)
                    
                    analysis_content = analysis_match.group(1).strip() if analysis_match else ""
                    email_content = email_match.group(1).strip() if email_match else ""
                    
                    analysis_content = re.sub(r"END_ANALYSIS", "", analysis_content, flags=re.IGNORECASE).strip()
                    email_content = re.sub(r"^```markdown\s*|^```\s*|```$", "", email_content, flags=re.IGNORECASE).strip()

                    if analysis_content and email_content:
                        st.session_state['out'] = f"### 📊 Analysis\n{analysis_content}\n\n### 📧 Email Draft\n```markdown\n{email_content}\n```"
                    elif analysis_content:
                        st.session_state['out'] = f"### ✅ Status\n{analysis_content}"
                    else:
                        st.session_state['out'] = f"### 🤖 Live Agent Response\n{raw_text}"
                except Exception as parse_err:
                    st.session_state['out'] = f"⚠️ Text parsing anomaly. Raw Agent Stream:\n\n{raw_text}"

    if 'out' in st.session_state and st.session_state['out']:
        st.write("---")
        st.markdown(st.session_state['out'])

except Exception as e:
    st.warning("🔄 Waiting for Backend Engine to establish connection... Ensure your FastAPI server is active.")
    st.stop()