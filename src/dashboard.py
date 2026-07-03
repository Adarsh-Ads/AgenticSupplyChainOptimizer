import sys
import os
import re

# Fix path resolution issues when running frontend/backend components across different directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import pandas as pd

# Must be the first Streamlit command executed to initialize layout
st.set_page_config(page_title="SCM AI Optimizer", layout="wide")

# Point to internal Docker network DNS if containerized; fall back to local dev loop
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip('/')

st.title("📦 Agentic Supply Chain Control Tower")

try:
    # Fetch current structural snapshot from FastAPI backend
    inventory_res = requests.get(f"{API_URL}/inventory")
    inventory_res.raise_for_status() 
    df = pd.DataFrame(inventory_res.json())
    
    # Simple feature engineering: derive stock runway based on historic daily velocity
    df['est_days_left'] = df['current_stock'] / 50 

    col_table, col_actions = st.columns([1.3, 1])

    with col_table:
        st.subheader("📊 Live Inventory Status")
        
        # Threshold heuristics for row styling: red (out of stock), yellow (low runway), green (stable)
        def apply_row_styles(row):
            if row['current_stock'] <= 0:
                return ['background-color: #721c24; color: #f8d7da; font-weight: bold'] * len(row)
            if row['est_days_left'] <= 5:
                return ['background-color: #856404; color: #fff3cd; font-weight: bold'] * len(row)
            return ['background-color: #155724; color: #d4edda'] * len(row)

        st.dataframe(df.style.apply(apply_row_styles, axis=1), use_container_width=True, height=500)

    with col_actions:
        st.subheader("🎯 Action Center")
        with st.container(border=True):
            product_list = df['product_id'].unique()
            target_id = st.selectbox("Select Product", product_list)
            target_days = st.slider("Target Buffer (Days)", 7, 90, 30)
            
            # Action gateway wrapped to prevent unnecessary backend/LLM evaluation overhead on page refresh
            if st.button("🚀 Run AI Analysis", use_container_width=True, type="primary"):
                
                matching_rows = df.loc[df['product_id'] == target_id, 'est_days_left'].values
                
                if len(matching_rows) > 0:
                    days_val = float(matching_rows[0])
                    payload = {"est_days_left": days_val, "target_days": float(target_days)}
                    
                    res = requests.post(f"{API_URL}/trigger/{target_id}", json=payload).json()
                    raw_text = res.get("analysis", "").strip()
                    
                    # Regex parsing layer: Uses non-consuming lookaheads to cleanly isolate the 
                    # structured segments (Analysis vs Email text block) from the raw LLM output stream.
                    try:
                        analysis_match = re.search(r"START_ANALYSIS\s*(.*?)(?=START_EMAIL|END_OUTPUT|END_ANALYSIS|$)", raw_text, re.DOTALL | re.IGNORECASE)
                        email_match = re.search(r"START_EMAIL\s*(.*?)(?=END_OUTPUT|END_EMAIL|START_SCHEMA|$)", raw_text, re.DOTALL | re.IGNORECASE)
                        
                        analysis_content = analysis_match.group(1).strip() if analysis_match else ""
                        email_content = email_match.group(1).strip() if email_match else ""
                        
                        # Strip formatting wrappers and rogue markdown markers from the captured group strings
                        analysis_content = re.sub(r"END_ANALYSIS", "", analysis_content, flags=re.IGNORECASE).strip()
                        email_content = re.sub(r"^```markdown\s*|^```\s*|```$", "", email_content, flags=re.IGNORECASE).strip()

                        # Cache parsed variables inside session state to survive widget state refreshes
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
    # Gracefully intercept network drops during container startup phases
    st.warning("🔄 Waiting for Backend Engine to establish connection... Ensure your FastAPI server is active.")
    st.stop()