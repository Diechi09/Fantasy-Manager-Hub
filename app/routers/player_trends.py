from fastapi import APIRouter
router = APIRouter()

@router.get("/player_trends")
def player_trends():
    return {"ok": True, "msg": "player trends placeholder"}
