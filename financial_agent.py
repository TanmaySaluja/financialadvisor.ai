import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "client_advisory_logs.csv"

load_dotenv()


class FinancialState(TypedDict):
    client_name: str
    age: int
    income: float
    expenses: float
    debt: float
    rent: float
    emergency_fund: float
    risk_profile: str
    status: str
    surplus_amount: float
    expert_path: str
    final_plan: str
    chat_history: list
    data_gathering_complete: bool
    user_message: str


def _get_llm():
    if not os.environ.get("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return ChatGroq(temperature=0, model="llama-3.3-70b-versatile")


llm = None


def intake_node(state: FinancialState):
    income = state["income"]
    expenses = state["expenses"]
    surplus = income - expenses
    status = "deficit" if surplus < 0 else "surplus"
    return {"status": status, "surplus_amount": surplus}


def extract_financial_metrics(chat_history: list, current_rent: float, current_ef: float, current_rp: str) -> dict:
    if not chat_history:
        return {"rent": current_rent, "emergency_fund": current_ef, "risk_profile": current_rp}

    history_str = ""
    for msg in chat_history:
        role = "Client" if msg["role"] == "user" else "Advisor"
        history_str += f"{role}: {msg['content']}\n"

    prompt = (
        "You are an assistant that extracts financial metrics from a conversation history.\n"
        "Inspect the history and extract the client's:\n"
        "1. Monthly Rent (as a float/number)\n"
        "2. Emergency Fund (as a float/number)\n"
        "3. Risk Profile (must be one of: 'low', 'moderate', 'high')\n\n"
        f"Conversation history:\n{history_str}\n\n"
        f"If a metric is not mentioned in the history or is not clear, use the current default value (Rent: {current_rent}, Emergency Fund: {current_ef}, Risk Profile: {current_rp}).\n"
        "Output ONLY a valid JSON object with keys 'rent', 'emergency_fund', and 'risk_profile'. Do not include any markdown styling or extra text. Example:\n"
        '{"rent": 15000.0, "emergency_fund": 45000.0, "risk_profile": "high"}'
    )
    try:
        response = _get_llm().invoke([SystemMessage(content=prompt)])
        import json
        clean_content = response.content.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        rp = data.get("risk_profile", current_rp).lower().strip()
        if rp not in ("low", "moderate", "high"):
            rp = current_rp
        return {
            "rent": float(data.get("rent", current_rent)),
            "emergency_fund": float(data.get("emergency_fund", current_ef)),
            "risk_profile": rp
        }
    except Exception:
        return {"rent": current_rent, "emergency_fund": current_ef, "risk_profile": current_rp}


def conversational_advisor_node(state: FinancialState):
    user_msg = state.get("user_message", "").strip()
    chat_history = list(state.get("chat_history", []))

    # Append user response if present
    if user_msg:
        chat_history.append({"role": "user", "content": user_msg})

    # Extract rent/emergency fund/risk profile from conversation history
    current_rent = state.get("rent", 0.0)
    current_ef = state.get("emergency_fund", 0.0)
    current_rp = state.get("risk_profile", "moderate")
    extracted = extract_financial_metrics(chat_history, current_rent, current_ef, current_rp)
    rent = extracted["rent"]
    ef = extracted["emergency_fund"]
    rp = extracted["risk_profile"]

    # If user explicitly wants to stop, finalize data gathering immediately
    if user_msg.lower() == "stop":
        return {
            "chat_history": chat_history,
            "data_gathering_complete": True,
            "rent": rent,
            "emergency_fund": ef,
            "risk_profile": rp
        }

    # Format history for the LLM
    history_str = ""
    for msg in chat_history:
        role = "Client" if msg["role"] == "user" else "Advisor"
        history_str += f"{role}: {msg['content']}\n"

    rent_str = "Not provided yet (ask for it)" if rent == 0 else f"₹{rent}"
    ef_str = "Not provided yet (ask for it)" if ef == 0 else f"₹{ef}"

    prompt = (
        f"You are a sharp, empathetic, and professional human financial advisor. You are interviewing the client to gather information "
        f"necessary to build an institutional-grade wealth and budget strategy. Here is the client's current profile:\n"
        f"- Name: {state['client_name']}\n"
        f"- Age: {state['age']}\n"
        f"- Monthly Income: ₹{state['income']}\n"
        f"- Monthly Expenses: ₹{state['expenses']}\n"
        f"- Overall Debt: ₹{state.get('debt', 0.0)}\n"
        f"- Monthly Rent: {rent_str}\n"
        f"- Emergency Fund: {ef_str}\n"
        f"- Risk Profile: {rp}\n\n"
        f"Here is the conversation history so far:\n{history_str}\n"
        "Your task is to inspect the profile for warning signs, analyze their situation, and dynamically interview the user. Specifically:\n"
        f"1. Suggest an age-based risk bearing capacity based on their age of {state['age']} (using guidelines like the '100 minus age' rule to suggest high/moderate/low risk) and ask if they would like to adopt it or adjust their profile.\n"
        "2. Gather missing variables such as monthly rent, emergency fund, financial goal horizons, and number of dependents. Since Overall Debt is provided in the onboarding, you MUST actively discuss this overall debt with the client, analyze its impact, and ask for their Monthly EMIs, interest rates, or repayment details associated with this debt.\n"
        "3. Deduce/Clarify Stated Expenses: If they provide a rent amount, check or clarify if their initial 'Monthly Expenses' figure already includes rent, so you can correctly define and calculate their true surplus.\n\n"
        "STRICT CONSTRAINTS:\n"
        "- Be extremely concise. Keep your responses limited to 1 or 2 short, punchy sentences maximum.\n"
        "- Do NOT explain rules, name formulas, list steps, or use conversational fluff/filler. Get straight to the point.\n"
        "- Converse naturally like a top-tier advisor, but with directness. Ask the question or make your observation immediately.\n"
        "- Do NOT repeat questions that have already been asked or refer to details that have already been answered in the history.\n"
        "- Do NOT recap or repeat the user's previous answers in your preamble.\n"
        "- If a variable is already populated in the profile or discussed in the history, do NOT ask for it again.\n"
        "- Ask exactly ONE sharp, probing question at a time. Do NOT output a final plan yet.\n\n"
        "If you have gathered all necessary information including rent, emergency fund, and agreed on the risk profile (or if there are at least 4 turns of questions and answers), "
        "reply with EXACTLY the word 'INTAKE_COMPLETE' to signal that you are ready to generate the final plan. Otherwise, "
        "ask exactly ONE sharp, probing question."
    )

    response = _get_llm().invoke([SystemMessage(content=prompt)])
    content = response.content.strip()

    if "INTAKE_COMPLETE" in content:
        return {
            "chat_history": chat_history,
            "data_gathering_complete": True,
            "rent": rent,
            "emergency_fund": ef,
            "risk_profile": rp
        }

    chat_history.append({"role": "assistant", "content": content})
    return {
        "chat_history": chat_history,
        "data_gathering_complete": False,
        "rent": rent,
        "emergency_fund": ef,
        "risk_profile": rp
    }


def recovery_node(state: FinancialState):
    history_summary = ""
    if state.get("chat_history"):
        history_summary = "\nHere is additional context gathered during our interview:\n"
        for msg in state["chat_history"]:
            role = "Client" if msg["role"] == "user" else "Advisor"
            history_summary += f"{role}: {msg['content']}\n"

    prompt = (
        f"You are a sharp, probing, and strict financial advisor. {state['client_name']} (age {state['age']}) is in a monthly deficit of "
        f"₹{abs(state['surplus_amount'])} (Income: ₹{state['income']}, Expenses: ₹{state['expenses']}, Debt/EMI: ₹{state.get('debt', 0.0)}, Rent: ₹{state['rent']}, Emergency Fund: ₹{state['emergency_fund']}).\n"
        f"{history_summary}\n"
        "Your task is to conduct a brutal audit and provide immediate tactical steps incorporating details from the conversation.\n\n"
        "Follow these rules:\n"
        "1. Critically Audit the Current State: Analyze the relation between Income, Expenses, Rent, and the Emergency Fund. If the rent takes up >30% of income, or if the emergency fund is too low relative to expenses, call it out and question its sustainability.\n"
        "2. Evaluate Expectations: Assess if the client's financial goals, expectations, or desired timelines discussed in the conversation are unrealistic or impossible given their monthly deficit and current numbers. If their expectations are too high/unrealistic, explicitly state this in the Audit and explain why.\n"
        "3. Restructure the Output: Format your entire response exactly into these two sections (use standard markdown headers):\n\n"
        "### [Advisor Audit]\n"
        "[A brutally honest, rapid review of their current numbers, rent sustainability, emergency fund status, and feasibility of goals/expectations]\n\n"
        "### [Provisional Tactical Blueprint]\n"
        "[Provide comprehensive personal finance advice, NOT just investments. Cover:\n"
        " - Budgeting & expense optimization (concrete strategies to cut deficit)\n"
        " - Debt management (tackling any outstanding liabilities/loans/EMIs discussed in the chat)\n"
        " - Risk & insurance planning (emergency fund scaling targets, health/life cover guidelines)\n"
        " - Tax optimization & long-term structural steps.\n"
        "If their expectations were flagged as unrealistic, suggest a better, realistic option/alternative strategy here]"
    )
    response = _get_llm().invoke([SystemMessage(content=prompt)])
    return {"final_plan": response.content}


def conservative_node(state: FinancialState):
    history_summary = ""
    if state.get("chat_history"):
        history_summary = "\nHere is additional context gathered during our interview:\n"
        for msg in state["chat_history"]:
            role = "Client" if msg["role"] == "user" else "Advisor"
            history_summary += f"{role}: {msg['content']}\n"

    prompt = (
        f"You are a sharp, probing, and conservative wealth manager. {state['client_name']} (age {state['age']}) has a monthly surplus of "
        f"₹{state['surplus_amount']} and low risk tolerance (Income: ₹{state['income']}, Expenses: ₹{state['expenses']}, Debt/EMI: ₹{state.get('debt', 0.0)}, Rent: ₹{state['rent']}, Emergency Fund: ₹{state['emergency_fund']}).\n"
        f"{history_summary}\n"
        "Your task is to conduct a critical audit and suggest a safe investment allocation incorporating details from the conversation.\n\n"
        "Follow these rules:\n"
        "1. Critically Audit the Current State: Analyze the relation between Income, Expenses, Rent, and the Emergency Fund. Call out if rent takes up >30% of income or if the emergency fund is insufficient relative to expenses.\n"
        "2. Evaluate Expectations: Assess if the client's financial goals, expectations, or desired returns/timelines discussed in the conversation are unrealistic or impossible given their low risk tolerance, monthly surplus, and numbers. If their expectations are too high/unrealistic, explicitly state this in the Audit and explain why.\n"
        "3. Restructure the Output: Format your entire response exactly into these two sections (use standard markdown headers):\n\n"
        "### [Advisor Audit]\n"
        "[A brutally honest, rapid review of their current numbers, rent sustainability, emergency fund status, and feasibility of goals/expectations]\n\n"
        "### [Provisional Tactical Blueprint]\n"
        "[Provide comprehensive personal finance advice, NOT just investments. Cover:\n"
        " - Asset Allocation (safe, low-risk allocation e.g. FDs, Government Bonds, Index Funds, keeping rent/emergency savings in mind)\n"
        " - Expense & liability management (tackling any outstanding loans/EMIs discussed in the chat)\n"
        " - Risk & insurance planning (emergency fund scaling targets, health/life cover guidelines)\n"
        " - Tax optimization & long-term structural steps.\n"
        "If their expectations were flagged as unrealistic, suggest a better, realistic option/alternative strategy here]"
    )
    response = _get_llm().invoke([SystemMessage(content=prompt)])
    return {"final_plan": response.content}


def aggressive_node(state: FinancialState):
    history_summary = ""
    if state.get("chat_history"):
        history_summary = "\nHere is additional context gathered during our interview:\n"
        for msg in state["chat_history"]:
            role = "Client" if msg["role"] == "user" else "Advisor"
            history_summary += f"{role}: {msg['content']}\n"

    prompt = (
        f"You are a sharp, probing, and growth-focused wealth manager. {state['client_name']} (age {state['age']}) has a monthly surplus of "
        f"₹{state['surplus_amount']} and {state['risk_profile']} risk tolerance (Income: ₹{state['income']}, Expenses: ₹{state['expenses']}, Debt/EMI: ₹{state.get('debt', 0.0)}, Rent: ₹{state['rent']}, Emergency Fund: ₹{state['emergency_fund']}).\n"
        f"{history_summary}\n"
        "Your task is to conduct a critical audit and suggest an aggressive growth investment allocation incorporating details from the conversation.\n\n"
        "Follow these rules:\n"
        "1. Critically Audit the Current State: Analyze the relation between Income, Expenses, Rent, and the Emergency Fund. Call out if rent takes up >30% of income or if the emergency fund is insufficient relative to expenses.\n"
        "2. Evaluate Expectations: Assess if the client's financial goals, expectations, or desired returns/timelines discussed in the conversation are unrealistic or impossible given their risk profile, monthly surplus, and numbers. If their expectations are too high/unrealistic, explicitly state this in the Audit and explain why.\n"
        "3. Restructure the Output: Format your entire response exactly into these two sections (use standard markdown headers):\n\n"
        "### [Advisor Audit]\n"
        "[A brutally honest, rapid review of their current numbers, rent sustainability, emergency fund status, and feasibility of goals/expectations]\n\n"
        "### [Provisional Tactical Blueprint]\n"
        "[Provide comprehensive personal finance advice, NOT just investments. Cover:\n"
        " - Asset Allocation (aggressive equity, mutual fund, and growth asset allocation while scaling emergency reserves)\n"
        " - Debt & liability management (tackling any outstanding loans/EMIs discussed in the chat)\n"
        " - Risk & insurance planning (emergency fund scaling targets, health/life cover guidelines)\n"
        " - Tax optimization & long-term structural steps.\n"
        "If their expectations were flagged as unrealistic, suggest a better, realistic option/alternative strategy here]"
    )
    response = _get_llm().invoke([SystemMessage(content=prompt)])
    return {"final_plan": response.content}


def action_node(state: FinancialState):
    if not LOG_FILE.exists():
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Client Name", "Status", "Risk Profile", "Action Taken"])

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            state["client_name"],
            state["status"],
            state["risk_profile"],
            "Success - Plan Generated & Dispatched",
        ])

    return state


def adaptive_router_node(state: FinancialState):
    history_summary = ""
    for msg in state.get("chat_history", []):
        role = "Client" if msg["role"] == "user" else "Advisor"
        history_summary += f"{role}: {msg['content']}\n"

    # Sum rent and base expenses to get total monthly liabilities
    total_expenses = state.get("expenses", 0.0) + state.get("rent", 0.0)
    surplus_val = state["income"] - total_expenses
    status_val = "deficit" if surplus_val < 0 else "surplus"

    prompt = (
        "You are an expert financial router. Your task is to dynamically analyze the client's financial state and conversation "
        "to route them to the most appropriate advisory node. Here is the client's data:\n"
        f"- Income: ₹{state['income']}\n"
        f"- Base Expenses: ₹{state['expenses']}\n"
        f"- Rent: ₹{state['rent']}\n"
        f"- Overall Debt Liability: ₹{state.get('debt', 0.0)}\n"
        f"- Total Monthly Expenses: ₹{total_expenses}\n"
        f"- Monthly Cash Flow Surplus: ₹{surplus_val}\n"
        f"- Self-reported Risk Profile: {state['risk_profile']}\n"
        f"- Age: {state['age']}\n\n"
        f"Conversation Context:\n{history_summary}\n"
        "Decision Criteria:\n"
        "1. Select 'recovery' if the user is in a monthly deficit (Total Monthly Expenses > Income), has severe overall debts, or needs urgent budgeting/debt repair.\n"
        "2. Select 'conservative' if the user has low risk tolerance, is of advanced age, has high dependents, or has short-term critical goals.\n"
        "3. Select 'aggressive' if the user has a healthy surplus, high risk capacity, low overall debt, and long-term wealth goals.\n\n"
        "Reply with exactly one word from this list: recovery, conservative, aggressive."
    )
    
    try:
        response = _get_llm().invoke([SystemMessage(content=prompt)])
        decision = response.content.strip().lower()
        if "recovery" in decision:
            expert = "recovery"
        elif "conservative" in decision:
            expert = "conservative"
        elif "aggressive" in decision:
            expert = "aggressive"
        else:
            # Fallback
            expert = "recovery" if status_val == "deficit" else ("aggressive" if state["risk_profile"] in ("high", "moderate") else "conservative")
    except Exception:
        expert = "recovery" if status_val == "deficit" else ("aggressive" if state["risk_profile"] in ("high", "moderate") else "conservative")

    return {
        "expert_path": expert,
        "status": status_val,
        "surplus_amount": surplus_val
    }


def route_after_conversation(state: FinancialState) -> str:
    if state.get("data_gathering_complete", False):
        return "adaptive_router"
    return END


def route_after_router(state: FinancialState) -> str:
    path = state.get("expert_path", "conservative")
    if path == "recovery":
        return "recovery_node"
    elif path == "aggressive":
        return "aggressive_node"
    return "conservative_node"


def build_graph():
    builder = StateGraph(FinancialState)

    builder.add_node("intake", intake_node)
    builder.add_node("conversational_advisor", conversational_advisor_node)
    builder.add_node("adaptive_router", adaptive_router_node)
    builder.add_node("recovery_node", recovery_node)
    builder.add_node("conservative_node", conservative_node)
    builder.add_node("aggressive_node", aggressive_node)
    builder.add_node("action", action_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "conversational_advisor")
    
    builder.add_conditional_edges(
        "conversational_advisor",
        route_after_conversation,
        {
            "adaptive_router": "adaptive_router",
            END: END
        }
    )

    builder.add_conditional_edges(
        "adaptive_router",
        route_after_router,
        {
            "recovery_node": "recovery_node",
            "conservative_node": "conservative_node",
            "aggressive_node": "aggressive_node"
        }
    )

    builder.add_edge("recovery_node", "action")
    builder.add_edge("conservative_node", "action")
    builder.add_edge("aggressive_node", "action")
    builder.add_edge("action", END)

    return builder.compile()


agent_graph = build_graph()


def run_advisor(
    client_name: str,
    age: int,
    income: float,
    expenses: float,
    risk_profile: str,
    debt: float = 0.0,
    rent: float = 0.0,
    emergency_fund: float = 0.0,
    chat_history: list = None,
    user_message: str = ""
) -> dict:
    if chat_history is None:
        chat_history = []

    result = agent_graph.invoke({
        "client_name": client_name,
        "age": age,
        "income": income,
        "expenses": expenses,
        "debt": debt,
        "rent": rent,
        "emergency_fund": emergency_fund,
        "risk_profile": risk_profile,
        "chat_history": chat_history,
        "data_gathering_complete": False,
        "user_message": user_message
    })

    total_expenses = result.get("expenses", 0.0) + result.get("rent", 0.0)
    surplus_val = result["income"] - total_expenses
    status_val = "deficit" if surplus_val < 0 else "surplus"

    return {
        "client_name": result["client_name"],
        "age": result["age"],
        "income": result["income"],
        "expenses": result["expenses"],
        "debt": result.get("debt", 0.0),
        "total_expenses": total_expenses,
        "status": status_val,
        "surplus_amount": surplus_val,
        "rent": result["rent"],
        "emergency_fund": result["emergency_fund"],
        "risk_profile": result["risk_profile"],
        "expert_path": result.get("expert_path", "conservative"),
        "chat_history": result["chat_history"],
        "data_gathering_complete": result["data_gathering_complete"],
        "final_plan": result.get("final_plan", ""),
        "log_file": str(LOG_FILE),
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    test_client = {
        "client_name": "Tanmay",
        "age": 28,
        "income": 80000,
        "expenses": 50000,
        "rent": 15000,
        "emergency_fund": 45000,
        "risk_profile": "high",
        "chat_history": [],
        "user_message": ""
    }

    print(f"Running Financial AI Agent (intake stage) for {test_client['client_name']}...")
    output = run_advisor(**test_client)
    print("Advisor question: ", output["chat_history"][-1]["content"])

