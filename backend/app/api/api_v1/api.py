from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, users, catalogue, auction, orders

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include user management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include catalogue endpoints
api_router.include_router(catalogue.router, prefix="/catalogue", tags=["catalogue"])

# Include auction endpoints
api_router.include_router(auction.router, prefix="/auction", tags=["auction"])

# Include orders endpoints
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])

@api_router.get("/")
async def api_root():
    return {"message": "Auction E-commerce System API v1"}
 