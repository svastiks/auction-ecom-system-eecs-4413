from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, users

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include user management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

@api_router.get("/")
async def api_root():
    return {"message": "Auction E-commerce System API v1"}
