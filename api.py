from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from financial_agent import run_advisor

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Financial Advisory AI")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AdvisoryRequest(BaseModel):
    client_name: str = Field(min_length=1, max_length=100)
    age: int = Field(gt=0, lt=150)
    income: float = Field(gt=0)
    expenses: float = Field(ge=0)
    debt: float = Field(default=0.0, ge=0)
    rent: float = Field(default=0.0, ge=0)
    emergency_fund: float = Field(default=0.0, ge=0)
    risk_profile: str = Field(pattern="^(low|moderate|high)$")
    chat_history: list = Field(default_factory=list)
    user_message: str = Field(default="")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/advise")
async def advise(request: AdvisoryRequest):
    try:
        return run_advisor(
            client_name=request.client_name.strip(),
            age=request.age,
            income=request.income,
            expenses=request.expenses,
            debt=request.debt,
            rent=request.rent,
            emergency_fund=request.emergency_fund,
            risk_profile=request.risk_profile,
            chat_history=request.chat_history,
            user_message=request.user_message,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
