import traceback
from agno.agent import Agent
from agno.models.groq import Groq
import sqlite3
import os
from dotenv import load_dotenv
from src.agent_tools import get_supplier_details

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/inventory.db")

def forecast_stock_risk(product_id: str, est_days_left: float, target_days: float):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        product = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        conn.close()

        if not product:
            return {"analysis": "START_ANALYSIS\nError: Product not found.\nEND_OUTPUT"}

        # Linear projection math confirming baseline procurement shortfalls
        units_needed = max(0, (target_days - est_days_left) * 50)

        base_instructions = [
            "You are a strict data formatting script. You must output exactly according to the template markers.",
            "Do not include conversational introductions, conclusions, or markdown code blocks around the markers.",
            "",
            "START_ANALYSIS",
            f"To reach your {target_days:.1f}-day buffer, an order of {units_needed:.0f} units is required.",
        ]

        # DETERMINISTIC GUARDRAILS: Programmatic switch checks the threshold before passing context to the LLM.
        # This approach eliminates structural hallucination loops if procurement is not required.
        if units_needed > 0:
            supplier_info = get_supplier_details(product_id)
            if isinstance(supplier_info, dict):
                supplier_name = supplier_info.get("supplier_name", "General Supplier")
                supplier_email = supplier_info.get("supplier_email", "orders@supply-chain.com")
            else:
                supplier_name = "General Supplier"
                supplier_email = "orders@supply-chain.com"

            base_instructions.extend([
                "",
                "START_EMAIL",
                f"Subject: Immediate Procurement Order Request - {product_id}",
                f"Dear {supplier_name},",
                f"Please process an immediate warehouse dispatch order for {units_needed:.0f} units of Product ID: {product_id}.",
                f"Kindly confirm receipt and dispatch configurations to {supplier_email}.",
                "Best Regards,",
                "Automated Procurement Engine"
            ])
        
        base_instructions.append("\nEND_OUTPUT")

        # Zero-temperature configuration prevents token divergence and enforces strict protocol formatting compliance
        agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile", temperature=0.0),
            instructions=base_instructions
        )

        response = agent.run(f"Process schema for {product_id}")
        return {"analysis": response.content}

    except Exception as e:
        print("\n❌ BACKEND CRASH ENCOUNTERED:")
        traceback.print_exc()
        return {"analysis": f"START_ANALYSIS\nBackend Runtime Error: {str(e)}\nEND_OUTPUT"}