import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SCM AI Optimizer", layout="wide")
API_URL = "http://127.0.0.1:8000"

st.title("📦 Agentic Supply Chain Control Tower")

try:
    inventory_res = requests.get(f"{API_URL}/inventory")
    inventory_res.raise_for_status()
    df = pd.DataFrame(inventory_res.json())
    df['est_days_left'] = df['current_stock'] / 50 

    col_table, col_actions = st.columns([1.3, 1])

    with col_table:
        st.subheader("📊 Live Inventory Status")
        def apply_row_styles(row):
            if row['current_stock'] <= 0: return ['background-color: #721c24; color: white'] * len(row)
            if row['est_days_left'] < 10: return ['background-color: #856404; color: white'] * len(row)
            return [''] * len(row)
        st.dataframe(df.style.apply(apply_row_styles, axis=1), use_container_width=True, height=500)

    with col_actions:
        st.subheader("🎯 Action Center")
        with st.container(border=True):
            target_id = st.selectbox("Select Product", df['product_id'].unique())
            target_days = st.slider("Target Buffer (Days)", 7, 90, 30)
            
            if st.button("🚀 Run AI Analysis", use_container_width=True, type="primary"):
                days_val = float(df.loc[df['product_id'] == target_id, 'est_days_left'].values[0])
                payload = {"est_days_left": days_val, "target_days": float(target_days)}
                
                res = requests.post(f"{API_URL}/trigger/{target_id}", json=payload).json()
                raw_text = res.get("analysis", "").strip()
                
                # --- BULLETPROOF REGEX PARSING ENGINE ---
                # Looks for structural markers regardless of markdown formatting, newlines, or casing
                try:
                    analysis_match = re.search(r"START_ANALYSIS\s*(.*?)(?=START_EMAIL|END_OUTPUT|$)", raw_text, re.DOTALL | re.IGNORECASE)
                    email_match = re.search(r"START_EMAIL\s*(.*?)(?=END_OUTPUT|$)", raw_text, re.DOTALL | re.IGNORECASE)
                    
                    analysis_content = analysis_match.group(1).strip() if analysis_match else ""
                    email_content = email_match.group(1).strip() if email_match else ""
                    
                    # Ensure markdown wrappers like backticks inside email output don't break lookups
                    email_content = re.sub(r"^```markdown\s*|^```\s*|```$", "", email_content, flags=re.IGNORECASE).strip()

                    if analysis_content and email_content:
                        st.session_state['out'] = f"### 📊 Analysis\n{analysis_content}\n\n### 📧 Email Draft\n```markdown\n{email_content}\n```"
                    elif analysis_content:
                        st.session_state['out'] = f"### ✅ Status\n{analysis_content}"
                    else:
                        # Defensive backup: display whatever text came back if regex capturing groups are empty
                        st.session_state['out'] = f"### 🤖 Live Agent Response\n{raw_text}"
                except Exception as parse_err:
                    st.session_state['out'] = f"⚠️ Text parsing anomaly. Raw Agent Stream:\n\n{raw_text}"

    # Clear spacing and cleanly render output stream
    if 'out' in st.session_state and st.session_state['out']:
        st.write("---")
        st.markdown(st.session_state['out'])

except Exception as e:
    st.warning("🔄 Waiting for Backend Engine to establish connection... Ensure your FastAPI server is active.")
    st.stop()