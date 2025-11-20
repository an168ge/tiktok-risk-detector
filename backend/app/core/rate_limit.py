"""
限流中间件
"""
from fastapi import Request, HTTPException, status
from app.core.cache import redis_client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """限流器"""
    
    def __init__(
        self,
        requests: int = settings.RATE_LIMIT_REQUESTS,
        period: int = settings.RATE_LIMIT_PERIOD
    ):
        self.requests = requests
        self.period = period
    
    async def check_rate_limit(self, client_ip: str) -> bool:
        """检查是否超过限流"""
        if not settings.RATE_LIMIT_ENABLED:
            return True
        
        key = f"rate_limit:{client_ip}"
        
        try:
            # 获取当前计数
            count = await redis_client.get(key)
            
            if count is None:
                # 首次请求，设置计数器
                await redis_client.set(key, 1, ttl=self.period)
                return True
            
            if int(count) >= self.requests:
                # 超过限流
                return False
            
            # 增加计数
            await redis_client.increment(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # 出错时允许请求通过
            return True
    
    async def get_remaining_requests(self, client_ip: str) -> int:
        """获取剩余请求次数"""
        key = f"rate_limit:{client_ip}"
        
        try:
            count = await redis_client.get(key)
            if count is None:
                return self.requests
            return max(0, self.requests - int(count))
        except Exception as e:
            logger.error(f"Get remaining requests error: {e}")
            return self.requests


# 全局限流器实例
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """依赖注入：检查限流"""
    client_ip = request.client.host
    
    if not await rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    return True
