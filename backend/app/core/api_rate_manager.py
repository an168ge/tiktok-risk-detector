"""
API速率管理器
管理第三方API的调用配额，优化使用策略
"""
import logging
from typing import Optional, Literal
from datetime import datetime, timezone
from app.core.cache import redis_client
from app.config import settings

logger = logging.getLogger(__name__)

APIProvider = Literal["iphub", "ipqualityscore", "proxycheck"]


class APIRateManager:
    """API速率管理器"""

    def __init__(self):
        # API配额配置
        self.quotas = {
            "iphub": {
                "daily_limit": 1000,      # 每天1000次
                "daily_usage": 990,       # 每天使用990次（留10次余量）
                "priority": 1             # 优先级1（最高）
            },
            "ipqualityscore": {
                "monthly_limit": 5000,    # 每月5000次
                "daily_usage": 150,       # 每天使用150次
                "priority": 2             # 优先级2
            },
            "proxycheck": {
                "daily_limit": 1000,      # 免费API，每天1000次
                "daily_usage": 999,       # 几乎无限使用
                "priority": 3             # 优先级3（最低，备用）
            }
        }

        # Redis键前缀
        self.key_prefix = "api_rate"

    def _get_daily_key(self, provider: APIProvider) -> str:
        """获取每日计数器的Redis键"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.key_prefix}:daily:{provider}:{today}"

    def _get_monthly_key(self, provider: APIProvider) -> str:
        """获取每月计数器的Redis键"""
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return f"{self.key_prefix}:monthly:{provider}:{month}"

    async def get_daily_usage(self, provider: APIProvider) -> int:
        """获取今日使用次数"""
        key = self._get_daily_key(provider)
        count = await redis_client.get(key)
        return int(count) if count else 0

    async def get_monthly_usage(self, provider: APIProvider) -> int:
        """获取本月使用次数"""
        key = self._get_monthly_key(provider)
        count = await redis_client.get(key)
        return int(count) if count else 0

    async def increment_usage(self, provider: APIProvider):
        """增加使用计数"""
        # 增加每日计数
        daily_key = self._get_daily_key(provider)
        daily_count = await redis_client.get(daily_key)

        if daily_count is None:
            # 首次使用，设置过期时间为当天结束
            now = datetime.now(timezone.utc)
            midnight = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            ttl = int((midnight - now).total_seconds()) + 1
            await redis_client.set(daily_key, 1, ttl=ttl)
        else:
            await redis_client.increment(daily_key)

        # 如果是月度配额的API，也增加月度计数
        if provider == "ipqualityscore":
            monthly_key = self._get_monthly_key(provider)
            monthly_count = await redis_client.get(monthly_key)

            if monthly_count is None:
                # 首次使用，设置过期时间为当月结束
                now = datetime.now(timezone.utc)
                # 计算下个月第一天
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0)
                else:
                    next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0)
                ttl = int((next_month - now).total_seconds())
                await redis_client.set(monthly_key, 1, ttl=ttl)
            else:
                await redis_client.increment(monthly_key)

        logger.info(f"API usage incremented: {provider}")

    async def can_use_api(self, provider: APIProvider) -> bool:
        """检查是否可以使用该API"""
        config = self.quotas.get(provider)
        if not config:
            return False

        # 检查每日配额
        daily_usage = await self.get_daily_usage(provider)
        if daily_usage >= config["daily_usage"]:
            logger.warning(f"Daily quota exceeded for {provider}: {daily_usage}/{config['daily_usage']}")
            return False

        # 对于月度配额的API，额外检查月度限制
        if provider == "ipqualityscore":
            monthly_usage = await self.get_monthly_usage(provider)
            if monthly_usage >= config["monthly_limit"]:
                logger.warning(f"Monthly quota exceeded for {provider}: {monthly_usage}/{config['monthly_limit']}")
                return False

        return True

    async def select_best_api(self) -> Optional[APIProvider]:
        """
        选择最佳的API提供商

        策略：
        1. 优先使用IPHub（每天990次）
        2. IPHub用完后，使用IPQualityScore（每天150次）
        3. 都用完后，降级到免费的proxycheck

        返回：
            可用的API提供商名称，如果都不可用则返回None
        """
        # 按优先级排序
        providers: list[APIProvider] = ["iphub", "ipqualityscore", "proxycheck"]

        for provider in providers:
            # 检查是否配置了API密钥（proxycheck除外，它是免费的）
            if provider == "iphub" and not settings.IPHUB_API_KEY:
                logger.debug(f"Skipping {provider}: API key not configured")
                continue

            if provider == "ipqualityscore" and not settings.IPQUALITYSCORE_API_KEY:
                logger.debug(f"Skipping {provider}: API key not configured")
                continue

            # 检查配额
            if await self.can_use_api(provider):
                logger.info(f"Selected API provider: {provider}")
                return provider

        logger.error("No available API provider")
        return None

    async def get_usage_stats(self) -> dict:
        """获取所有API的使用统计"""
        stats = {}

        for provider in ["iphub", "ipqualityscore", "proxycheck"]:
            config = self.quotas[provider]
            daily_usage = await self.get_daily_usage(provider)

            provider_stats = {
                "daily_usage": daily_usage,
                "daily_limit": config.get("daily_limit", config["daily_usage"]),
                "daily_remaining": config["daily_usage"] - daily_usage,
                "priority": config["priority"]
            }

            # 月度配额的API添加月度统计
            if provider == "ipqualityscore":
                monthly_usage = await self.get_monthly_usage(provider)
                provider_stats.update({
                    "monthly_usage": monthly_usage,
                    "monthly_limit": config["monthly_limit"],
                    "monthly_remaining": config["monthly_limit"] - monthly_usage
                })

            stats[provider] = provider_stats

        return stats

    async def reset_daily_quota(self, provider: APIProvider):
        """重置每日配额（用于测试或手动重置）"""
        key = self._get_daily_key(provider)
        await redis_client.delete(key)
        logger.info(f"Daily quota reset for {provider}")

    async def reset_monthly_quota(self, provider: APIProvider):
        """重置月度配额（用于测试或手动重置）"""
        key = self._get_monthly_key(provider)
        await redis_client.delete(key)
        logger.info(f"Monthly quota reset for {provider}")


# 全局API速率管理器实例
api_rate_manager = APIRateManager()