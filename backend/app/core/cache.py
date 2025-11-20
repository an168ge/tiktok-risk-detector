"""
Redis缓存管理
"""
import json
from typing import Optional, Any
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.default_ttl = settings.REDIS_CACHE_TTL
    
    async def connect(self):
        """连接Redis"""
        if not self.redis:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connected")
    
    async def close(self):
        """关闭连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def ping(self) -> bool:
        """测试连接"""
        if not self.redis:
            await self.connect()
        return await self.redis.ping()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.redis:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存"""
        if not self.redis:
            await self.connect()
        
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self.redis:
            await self.connect()
        
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False
    
    def make_key(self, *args) -> str:
        """生成缓存键"""
        return ":".join(str(arg) for arg in args)


# 全局Redis客户端
redis_client = RedisCache()
