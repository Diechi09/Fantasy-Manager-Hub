from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import applogin, assistant_coach, player_trends, trade_calculator, roster_analysis

app = FastAPI(title="Fantasy Manager Hub")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/welcome")
@app.get("/")
def root():
    WELCOME = {"title":"Fantasy Manager Hub","message":"Win trades, track trends, and optimize your roster."}
    return WELCOME

app.include_router(applogin.router, prefix="/applogin", tags=["applogin"])
app.include_router(assistant_coach.router, prefix="/assistant_coach", tags=["assistant_coach"])
app.include_router(roster_analysis.router, prefix="/roster_analysis", tags=["roster_analysis"])
app.include_router(player_trends.router, prefix="/player_trends", tags=["player_trends"])
app.include_router(trade_calculator.router, prefix="/trade_calculator", tags=["trade_calculator"])
