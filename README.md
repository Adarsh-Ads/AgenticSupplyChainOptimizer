# 📦 Agentic Supply Chain Optimizer

An AI-powered inventory management system using **XGBoost** for forecasting and **Llama-3 (Groq)** for agentic decision-making.

## 🚀 Features
- **Predictive Engine:** Uses XGBoost to forecast stock-out risks.
- **AI Agent:** A Groq-powered agent that drafts supplier emails automatically.
- **FastAPI Backend:** Serves data and triggers agentic workflows.
- **Streamlit Dashboard:** Real-time visualization of stock health.

## 🛠️ Setup
1. Clone the repo: `git clone <your-repo-url>`
2. Install requirements: `pip install -r requirements.txt`
3. Add your `GROQ_API_KEY` to a `.env` file.
4. Initialize data: `python src/database.py`
5. Run Backend: `uvicorn main:app --app-dir src`
6. Run Dashboard: `streamlit run src/dashboard.py`