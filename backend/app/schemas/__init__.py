"""
数据验证Schema
"""
from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"           # 低风险 80-100
    MEDIUM = "medium"     # 中风险 60-79
    HIGH = "high"         # 高风险 40-59
    CRITICAL = "critical" # 严重风险 0-39


class IPType(str, Enum):
    """IP类型"""
    RESIDENTIAL = "residential"  # 住宅IP
    DATACENTER = "datacenter"    # 数据中心IP
    MOBILE = "mobile"            # 移动IP
    HOSTING = "hosting"          # 托管IP
    VPN = "vpn"                  # VPN IP
    PROXY = "proxy"              # 代理IP
    UNKNOWN = "unknown"          # 未知


class DetectionStatus(str, Enum):
    """检测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== 请求Schema ====================

class DetectionRequest(BaseModel):
    """检测请求"""
    user_agent: str = Field(..., description="User-Agent字符串")
    timezone: str = Field(..., description="时区")
    language: str = Field(..., description="浏览器语言")
    screen_resolution: str = Field(..., description="屏幕分辨率")
    color_depth: int = Field(..., description="颜色深度")
    platform: str = Field(..., description="平台信息")
    
    # 可选的额外信息
    canvas_fingerprint: Optional[str] = Field(None, description="Canvas指纹")
    webgl_fingerprint: Optional[str] = Field(None, description="WebGL指纹")
    fonts: Optional[List[str]] = Field(None, description="字体列表")
    plugins: Optional[List[str]] = Field(None, description="插件列表")
    webrtc_ips: Optional[List[str]] = Field(None, description="WebRTC暴露的IP")
    dns_servers: Optional[List[str]] = Field(None, description="DNS服务器列表")
    has_webdriver: Optional[bool] = Field(None, description="是否检测到WebDriver")
    is_mobile: Optional[bool] = Field(None, description="是否移动设备")
    hardware_concurrency: Optional[int] = Field(None, description="CPU核心数")
    device_memory: Optional[int] = Field(None, description="设备内存(GB)")
    max_touch_points: Optional[int] = Field(None, description="最大触摸点数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
                "timezone": "America/Los_Angeles",
                "language": "en-US",
                "screen_resolution": "375x812",
                "color_depth": 24,
                "platform": "iPhone",
                "hardware_concurrency": 6,
                "max_touch_points": 5
            }
        }


# ==================== IP检测相关Schema ====================

class IPInfo(BaseModel):
    """IP基础信息"""
    ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    as_name: Optional[str] = None


class IPQuality(BaseModel):
    """IP质量评估"""
    ip_type: IPType
    is_vpn: bool
    is_proxy: bool
    is_datacenter: bool
    is_tor: bool = False
    is_hosting: bool = False
    reputation_score: float = Field(..., ge=0, le=100)
    fraud_score: float = Field(..., ge=0, le=100)
    abuse_confidence_score: float = Field(default=0, ge=0, le=100)


class IPDetectionResult(BaseModel):
    """IP检测结果"""
    info: IPInfo
    quality: IPQuality
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== DNS检测相关Schema ====================

class DNSServer(BaseModel):
    """DNS服务器信息"""
    ip: str
    location: Optional[str] = None
    provider: Optional[str] = None


class DNSDetectionResult(BaseModel):
    """DNS检测结果"""
    dns_servers: List[DNSServer]
    leak_detected: bool
    leak_severity: str  # none, low, medium, high
    vpn_dns_match: bool
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== WebRTC检测相关Schema ====================

class WebRTCDetectionResult(BaseModel):
    """WebRTC检测结果"""
    local_ips: List[str]
    public_ips: List[str]
    leak_detected: bool
    leak_severity: str  # none, low, medium, high
    real_ip_exposed: bool
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== 指纹检测相关Schema ====================

class BasicFingerprint(BaseModel):
    """基础指纹信息"""
    user_agent: str
    platform: str
    language: str
    timezone: str
    screen_resolution: str
    color_depth: int
    do_not_track: Optional[bool] = None
    cookies_enabled: bool = True


class AdvancedFingerprint(BaseModel):
    """高级指纹信息"""
    canvas_fingerprint: Optional[str] = None
    webgl_fingerprint: Optional[str] = None
    audio_fingerprint: Optional[str] = None
    fonts_hash: Optional[str] = None
    plugins_hash: Optional[str] = None


class FingerprintConsistency(BaseModel):
    """指纹一致性分析"""
    os_ua_match: bool  # 操作系统与UA匹配
    resolution_device_match: bool  # 分辨率与设备匹配
    language_location_match: bool  # 语言与位置匹配
    timezone_location_match: bool  # 时区与位置匹配
    overall_consistency: float = Field(..., ge=0, le=100)


class FingerprintDetectionResult(BaseModel):
    """指纹检测结果"""
    basic: BasicFingerprint
    advanced: Optional[AdvancedFingerprint] = None
    consistency: FingerprintConsistency
    uniqueness_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== 设备检测相关Schema ====================

class DeviceInfo(BaseModel):
    """设备信息"""
    device_type: str  # mobile, tablet, desktop
    os: str
    os_version: Optional[str] = None
    browser: str
    browser_version: Optional[str] = None
    is_mobile: bool
    is_tablet: bool
    is_desktop: bool


class EmulatorDetection(BaseModel):
    """模拟器检测"""
    is_emulator: bool
    is_virtual_machine: bool
    is_headless_browser: bool
    confidence: float = Field(..., ge=0, le=100)
    detected_patterns: List[str] = []


class DeviceDetectionResult(BaseModel):
    """设备检测结果"""
    device: DeviceInfo
    emulator: EmulatorDetection
    consistency_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== 网络质量检测相关Schema ====================

class NetworkQuality(BaseModel):
    """网络质量"""
    latency_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    packet_loss: Optional[float] = None
    download_speed_mbps: Optional[float] = None
    upload_speed_mbps: Optional[float] = None


class TikTokConnectivity(BaseModel):
    """TikTok连接性测试"""
    main_domain_accessible: bool
    cdn_accessible: bool
    api_accessible: bool
    avg_latency_ms: Optional[float] = None
    connection_stable: bool


class NetworkDetectionResult(BaseModel):
    """网络检测结果"""
    quality: NetworkQuality
    tiktok_connectivity: TikTokConnectivity
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    issues: List[str] = []
    recommendations: List[str] = []


# ==================== 综合报告Schema ====================

class RiskScoreBreakdown(BaseModel):
    """风险分数细分"""
    ip_score: float = Field(..., ge=0, le=100)
    privacy_score: float = Field(..., ge=0, le=100)
    fingerprint_score: float = Field(..., ge=0, le=100)
    device_score: float = Field(..., ge=0, le=100)
    network_score: float = Field(..., ge=0, le=100)


class Recommendation(BaseModel):
    """修复建议"""
    priority: str  # critical, high, medium, low
    category: str  # ip, dns, webrtc, fingerprint, device, network
    title: str
    description: str
    solution: str


class DetectionReport(BaseModel):
    """完整检测报告"""
    detection_id: str
    timestamp: datetime
    status: DetectionStatus
    
    # 各模块检测结果
    ip_result: Optional[IPDetectionResult] = None
    dns_result: Optional[DNSDetectionResult] = None
    webrtc_result: Optional[WebRTCDetectionResult] = None
    fingerprint_result: Optional[FingerprintDetectionResult] = None
    device_result: Optional[DeviceDetectionResult] = None
    network_result: Optional[NetworkDetectionResult] = None
    
    # 综合评分
    overall_score: float = Field(..., ge=0, le=100)
    overall_risk_level: RiskLevel
    score_breakdown: RiskScoreBreakdown
    
    # 问题和建议
    all_issues: List[str] = []
    recommendations: List[Recommendation] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "detection_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "completed",
                "overall_score": 75.5,
                "overall_risk_level": "medium"
            }
        }


# ==================== 响应Schema ====================

class APIResponse(BaseModel):
    """标准API响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: Dict[str, Any]
