"""Rate limiting service using Redis."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import redis.asyncio as redis

from app.config import get_settings
from app.models.schemas import UserTier

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Redis-based rate limiter for query and page processing limits.
    Tracks daily queries and monthly page processing per user.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.settings = settings
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            raise
    
    def _get_query_key(self, user_id: str) -> str:
        """Get Redis key for daily query count."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return f"rate_limit:queries:{user_id}:{date_str}"
    
    def _get_pages_key(self, user_id: str) -> str:
        """Get Redis key for monthly page count."""
        month_str = datetime.utcnow().strftime("%Y-%m")
        return f"rate_limit:pages:{user_id}:{month_str}"
    
    def _get_limits(self, user_tier: UserTier) -> Tuple[int, int]:
        """
        Get rate limits for user tier.
        Returns: (queries_per_day, pages_per_month)
        """
        if user_tier == UserTier.PREMIUM:
            return (
                self.settings.premium_tier_queries_per_day,
                self.settings.premium_tier_pages_per_month
            )
        else:  # FREE
            return (
                self.settings.free_tier_queries_per_day,
                self.settings.free_tier_pages_per_month
            )
    
    async def check_query_limit(self, user_id: str, user_tier: UserTier) -> Tuple[bool, int, int]:
        """
        Check if user can make another query.
        
        Returns:
            Tuple of (allowed, current_count, limit)
        """
        if not self.redis_client:
            logger.warning("Redis not available, allowing query")
            return True, 0, 999999
        
        query_limit, _ = self._get_limits(user_tier)
        key = self._get_query_key(user_id)
        
        try:
            # Get current count
            count_str = await self.redis_client.get(key)
            current_count = int(count_str) if count_str else 0
            
            # Check limit
            allowed = current_count < query_limit
            
            return allowed, current_count, query_limit
        
        except Exception as e:
            logger.error(f"Failed to check query limit: {e}")
            return True, 0, query_limit  # Allow on error
    
    async def increment_query_count(self, user_id: str) -> int:
        """
        Increment query count for user.
        Returns new count.
        """
        if not self.redis_client:
            return 0
        
        key = self._get_query_key(user_id)
        
        try:
            # Increment counter
            new_count = await self.redis_client.incr(key)
            
            # Set expiry to end of day if this is first query
            if new_count == 1:
                # Calculate seconds until end of day
                now = datetime.utcnow()
                tomorrow = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                seconds_until_reset = int((tomorrow - now).total_seconds())
                await self.redis_client.expire(key, seconds_until_reset)
            
            return new_count
        
        except Exception as e:
            logger.error(f"Failed to increment query count: {e}")
            return 0
    
    async def check_page_limit(self, user_id: str, user_tier: UserTier, pages: int) -> Tuple[bool, int, int]:
        """
        Check if user can process additional pages.
        
        Args:
            user_id: User identifier
            user_tier: User subscription tier
            pages: Number of pages to process
        
        Returns:
            Tuple of (allowed, current_count, limit)
        """
        if not self.redis_client:
            return True, 0, 999999
        
        _, page_limit = self._get_limits(user_tier)
        key = self._get_pages_key(user_id)
        
        try:
            count_str = await self.redis_client.get(key)
            current_count = int(count_str) if count_str else 0
            
            allowed = (current_count + pages) <= page_limit
            
            return allowed, current_count, page_limit
        
        except Exception as e:
            logger.error(f"Failed to check page limit: {e}")
            return True, 0, page_limit
    
    async def increment_page_count(self, user_id: str, pages: int) -> int:
        """
        Increment page processing count for user.
        Returns new count.
        """
        if not self.redis_client:
            return 0
        
        key = self._get_pages_key(user_id)
        
        try:
            # Increment counter
            new_count = await self.redis_client.incrby(key, pages)
            
            # Set expiry to end of month if this is first increment
            if new_count == pages:
                now = datetime.utcnow()
                # First day of next month
                if now.month == 12:
                    next_month = datetime(now.year + 1, 1, 1)
                else:
                    next_month = datetime(now.year, now.month + 1, 1)
                
                seconds_until_reset = int((next_month - now).total_seconds())
                await self.redis_client.expire(key, seconds_until_reset)
            
            return new_count
        
        except Exception as e:
            logger.error(f"Failed to increment page count: {e}")
            return 0
    
    async def get_usage_stats(self, user_id: str, user_tier: UserTier) -> dict:
        """Get current usage statistics for user."""
        query_limit, page_limit = self._get_limits(user_tier)
        
        # Get current counts
        query_key = self._get_query_key(user_id)
        page_key = self._get_pages_key(user_id)
        
        try:
            query_count_str = await self.redis_client.get(query_key) if self.redis_client else None
            page_count_str = await self.redis_client.get(page_key) if self.redis_client else None
            
            query_count = int(query_count_str) if query_count_str else 0
            page_count = int(page_count_str) if page_count_str else 0
            
            return {
                "tier": user_tier.value,
                "queries": {
                    "used": query_count,
                    "limit": query_limit,
                    "remaining": max(0, query_limit - query_count)
                },
                "pages": {
                    "used": page_count,
                    "limit": page_limit,
                    "remaining": max(0, page_limit - page_count)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                "tier": user_tier.value,
                "queries": {"used": 0, "limit": query_limit, "remaining": query_limit},
                "pages": {"used": 0, "limit": page_limit, "remaining": page_limit}
            }
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
