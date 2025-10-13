from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/")
async def api_root():
    return {"message": "Auction E-commerce System API v1"}
