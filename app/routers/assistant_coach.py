from fastapi import APIRouter
router = APIRouter()

@router.get("/assistant")
def assistant():
    return {"ok": True, "msg": "coach assistant placeholder"}
