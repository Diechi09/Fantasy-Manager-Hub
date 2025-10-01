from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Fantasy Manager Hub")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WELCOME = {"title":"Fantasy Manager Hub","message":"Win trades, track trends, and optimize your roster."}

@app.get("/")
def root():
    return WELCOME

@app.get("/health")
def health():
    return {"ok": True}
