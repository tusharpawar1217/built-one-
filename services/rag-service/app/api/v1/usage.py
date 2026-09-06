"""Usage tracking and statistics endpoints."""
import logging
from fastapi import APIRouter, Request, Query

from app.models.schemas import UserTier
from app.services.rate_limiter import RateLimiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_usage_stats(
    request: Request,
    user_id: str = Query(...),
    tier: str = Query(default="free")
):
    """
    Get usage statistics for a user.
    
    Returns:
        Current usage for queries and page processing
    """
    # Initialize rate limiter
    if not hasattr(request.app.state, "rate_limiter"):
        rate_limiter = RateLimiter()
        await rate_limiter.initialize()
        request.app.state.rate_limiter = rate_limiter
    else:
        rate_limiter = request.app.state.rate_limiter
    
    user_tier = UserTier.PREMIUM if tier.lower() == "premium" else UserTier.FREE
    
    stats = await rate_limiter.get_usage_stats(user_id, user_tier)
    
    return {
        "user_id": user_id,
        "stats": stats
    }
