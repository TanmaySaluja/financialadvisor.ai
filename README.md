# Bit By Bit Wealth

An autonomous, cognitive wealth management and budget planning pipeline built on Python, **LangGraph**, **FastAPI**, and **Groq Cloud (Llama-3.3-70B)**.

Bit By Bit Wealth replaces traditional, static financial spreadsheets and expensive human advisors with an interactive, multi-agent conversational chatbot and real-time dashboard.

---

## 🚀 Core Features

*   **Dual-Column Interactive Dashboard**: A glassmorphic web interface styled with space-indigo tones, geometric Plus Jakarta Sans typography, and live indicators.
*   **Live Surplus Calculator**: Client-side interactive surplus projections that dynamically subtract Monthly Expenses and Overall Debt from Income to display a real-time Savings Rate gauge.
*   **Adaptive Cognitive Routing**: LangGraph state-machine that routes user profiles through specialized expert nodes (`recovery`, `conservative`, or `aggressive`) based on their actual cash flow health.
*   **Personalized Blueprints**: Generates structured personal finance audits and tactical roadmaps detailing asset allocation, debt restructuring guidelines, and emergency fund scaling metrics.
*   **Secure Local Storage**: Automatically saves session histories, profile data, and reports in the browser's local storage for instant loading.

---

## 🛠️ Tech Stack

*   **Backend:** Python, LangGraph (StateGraph), FastAPI, Uvicorn, Pydantic
*   **Inference:** Groq Cloud API (`llama-3.3-70b-versatile`)
*   **Frontend:** HTML5, CSS3 (Vanilla Glassmorphism), JavaScript (ES6+), Marked.js

---

## 📂 Project Structure

```
├── static/
│   ├── index.html        # Main dashboard markup
│   ├── style.css         # Glassmorphism design tokens & styles
│   ├── app.js            # Frontend DOM operations & state controllers
│   └── dollar_bill.jpg   # Generated background transition asset
├── api.py                # FastAPI HTTP routing & schemas
├── financial_agent.py    # LangGraph StateGraph agent logic
├── requirements.txt      # Python dependencies list
├── .gitignore            # Git exclusion rules
├── .env.example          # Sample environment key variables file
└── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/TanmaySaluja/financialadvisor.ai.git
cd financialadvisor.ai
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Launch the Application
```bash
python -m uvicorn api:app --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser to start a consultation.
