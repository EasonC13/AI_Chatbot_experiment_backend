
from fastapi import APIRouter
router = APIRouter()

from db.mongodb import get_database
from core.config import DATABASE_NAME, USER_COL, MSG_COL

@router.get("/test")
async def test():
    print("HIHI")
    return "Hi Hi"
