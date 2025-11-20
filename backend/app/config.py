"""
应用配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "TikTok Risk Detector"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tiktok_detector"
    DATABASE_ECHO: bool = False
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1小时
    
    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 10  # 每分钟请求数
    RATE_LIMIT_PERIOD: int = 60    # 时间窗口（秒）
    
    # 第三方API配置
    IPHUB_API_KEY: Optional[str] = None
    IPQUALITYSCORE_API_KEY: Optional[str] = None
    IP2LOCATION_API_KEY: Optional[str] = None
    MAXMIND_LICENSE_KEY: Optional[str] = None
    
    # TikTok相关
    TIKTOK_API_DOMAIN: str = "www.tiktok.com"
    TIKTOK_CDN_DOMAINS: list = [
        "p16-sign-va.tiktokcdn.com",
        "p16-sign-sg.tiktokcdn.com",
        "v16-webapp.tiktok.com"
    ]
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 检测配置
    DETECTION_TIMEOUT: int = 30  # 检测超时时间（秒）
    MAX_CONCURRENT_DETECTIONS: int = 5  # 最大并发检测数
    
    # 数据保留配置
    DATA_RETENTION_DAYS: int = 30  # 数据保留天数
    
    # 风险评分权重
    RISK_WEIGHT_IP: float = 0.30
    RISK_WEIGHT_PRIVACY: float = 0.25
    RISK_WEIGHT_FINGERPRINT: float = 0.20
    RISK_WEIGHT_DEVICE: float = 0.15
    RISK_WEIGHT_NETWORK: float = 0.10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
