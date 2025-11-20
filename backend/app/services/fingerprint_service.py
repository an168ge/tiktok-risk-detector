"""
浏览器指纹分析服务
"""
import logging
import hashlib
import re
from typing import Dict, Any, List
from user_agents import parse as parse_user_agent

from app.schemas import (
    BasicFingerprint, AdvancedFingerprint, FingerprintConsistency,
    FingerprintDetectionResult, RiskLevel
)

logger = logging.getLogger(__name__)


class FingerprintService:
    """浏览器指纹分析服务"""
    
    # 常见屏幕分辨率（用于验证）
    COMMON_RESOLUTIONS = {
        # 桌面
        "1920x1080", "1366x768", "1440x900", "1536x864", "1280x720",
        # 移动设备
        "375x667", "414x896", "390x844", "360x640", "375x812",
        # 平板
        "768x1024", "810x1080", "820x1180"
    }
    
    # 常见时区
    COMMON_TIMEZONES = [
        "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Asia/Shanghai", "Asia/Tokyo",
        "Australia/Sydney"
    ]
    
    async def analyze_fingerprint(self, data: Dict[str, Any]) -> FingerprintDetectionResult:
        """完整指纹分析"""
        
        # 解析基础指纹
        basic = self._parse_basic_fingerprint(data)
        
        # 解析高级指纹
        advanced = self._parse_advanced_fingerprint(data)
        
        # 分析一致性
        consistency = await self._analyze_consistency(data, basic)
        
        # 计算唯一性分数
        uniqueness_score = self._calculate_uniqueness(data)
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(consistency, uniqueness_score)
        risk_level = self._get_risk_level(risk_score)
        
        # 识别问题
        issues = self._identify_issues(basic, consistency)
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return FingerprintDetectionResult(
            basic=basic,
            advanced=advanced,
            consistency=consistency,
            uniqueness_score=uniqueness_score,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
    
    def _parse_basic_fingerprint(self, data: Dict[str, Any]) -> BasicFingerprint:
        """解析基础指纹信息"""
        return BasicFingerprint(
            user_agent=data.get("user_agent", ""),
            platform=data.get("platform", ""),
            language=data.get("language", ""),
            timezone=data.get("timezone", ""),
            screen_resolution=data.get("screen_resolution", ""),
            color_depth=data.get("color_depth", 24),
            do_not_track=data.get("do_not_track"),
            cookies_enabled=data.get("cookies_enabled", True)
        )
    
    def _parse_advanced_fingerprint(self, data: Dict[str, Any]) -> AdvancedFingerprint:
        """解析高级指纹信息"""
        # 计算字体哈希
        fonts_hash = None
        if data.get("fonts"):
            fonts_str = ",".join(sorted(data["fonts"]))
            fonts_hash = hashlib.md5(fonts_str.encode()).hexdigest()
        
        # 计算插件哈希
        plugins_hash = None
        if data.get("plugins"):
            plugins_str = ",".join(sorted(data["plugins"]))
            plugins_hash = hashlib.md5(plugins_str.encode()).hexdigest()
        
        return AdvancedFingerprint(
            canvas_fingerprint=data.get("canvas_fingerprint"),
            webgl_fingerprint=data.get("webgl_fingerprint"),
            audio_fingerprint=data.get("audio_fingerprint"),
            fonts_hash=fonts_hash,
            plugins_hash=plugins_hash
        )
    
    async def _analyze_consistency(
        self,
        data: Dict[str, Any],
        basic: BasicFingerprint
    ) -> FingerprintConsistency:
        """分析指纹一致性"""
        
        # 解析User-Agent
        ua = parse_user_agent(basic.user_agent)
        
        # 1. 操作系统与User-Agent匹配
        os_ua_match = self._check_os_ua_match(basic.platform, ua)
        
        # 2. 分辨率与设备类型匹配
        resolution_device_match = self._check_resolution_device_match(
            basic.screen_resolution,
            ua.is_mobile,
            ua.is_tablet
        )
        
        # 3. 语言与地理位置匹配（需要IP地理位置信息）
        language_location_match = self._check_language_location_match(
            basic.language,
            data.get("ip_country_code", "")
        )
        
        # 4. 时区与地理位置匹配
        timezone_location_match = self._check_timezone_location_match(
            basic.timezone,
            data.get("ip_country_code", "")
        )
        
        # 计算总体一致性
        consistency_scores = [
            100 if os_ua_match else 0,
            100 if resolution_device_match else 0,
            100 if language_location_match else 50,  # 语言不匹配影响较小
            100 if timezone_location_match else 30   # 时区不匹配影响中等
        ]
        overall_consistency = sum(consistency_scores) / len(consistency_scores)
        
        return FingerprintConsistency(
            os_ua_match=os_ua_match,
            resolution_device_match=resolution_device_match,
            language_location_match=language_location_match,
            timezone_location_match=timezone_location_match,
            overall_consistency=overall_consistency
        )
    
    def _check_os_ua_match(self, platform: str, ua) -> bool:
        """检查操作系统与UA是否匹配"""
        platform_lower = platform.lower()
        
        # iOS设备
        if "iphone" in platform_lower or "ipad" in platform_lower:
            return ua.is_mobile and ua.os.family in ["iOS", "iPhone OS"]
        
        # Android设备
        if "android" in platform_lower:
            return ua.is_mobile and ua.os.family == "Android"
        
        # Windows
        if "win" in platform_lower:
            return ua.os.family == "Windows"
        
        # Mac
        if "mac" in platform_lower:
            return ua.os.family in ["Mac OS X", "macOS"]
        
        # Linux
        if "linux" in platform_lower:
            return ua.os.family == "Linux"
        
        return True  # 无法判断时认为匹配
    
    def _check_resolution_device_match(
        self,
        resolution: str,
        is_mobile: bool,
        is_tablet: bool
    ) -> bool:
        """检查分辨率与设备类型是否匹配"""
        try:
            width, height = map(int, resolution.split("x"))
            
            # 移动设备通常宽度 < 450px
            if is_mobile:
                return width <= 450 or height <= 450
            
            # 平板通常宽度在 450-900px
            if is_tablet:
                return 450 <= max(width, height) <= 1200
            
            # 桌面设备通常宽度 > 900px
            return max(width, height) > 900
            
        except (ValueError, AttributeError):
            return True  # 无法解析时认为匹配
    
    def _check_language_location_match(self, language: str, country_code: str) -> bool:
        """检查语言与地理位置是否匹配"""
        if not country_code:
            return True
        
        # 语言-国家映射（简化版）
        language_country_map = {
            "en": ["US", "GB", "CA", "AU", "NZ", "IE"],
            "zh": ["CN", "TW", "HK", "SG"],
            "ja": ["JP"],
            "ko": ["KR"],
            "es": ["ES", "MX", "AR", "CL", "CO"],
            "fr": ["FR", "CA", "BE", "CH"],
            "de": ["DE", "AT", "CH"],
            "ru": ["RU", "BY", "KZ"],
            "pt": ["BR", "PT"],
            "it": ["IT"],
            "ar": ["SA", "AE", "EG"]
        }
        
        # 提取语言代码（如 en-US -> en）
        lang_code = language.split("-")[0].lower()
        
        if lang_code in language_country_map:
            return country_code in language_country_map[lang_code]
        
        return True  # 未知语言认为匹配
    
    def _check_timezone_location_match(self, timezone: str, country_code: str) -> bool:
        """检查时区与地理位置是否匹配"""
        if not country_code or not timezone:
            return True
        
        # 时区-国家映射（简化版）
        timezone_country_map = {
            "America/New_York": ["US"],
            "America/Los_Angeles": ["US"],
            "America/Chicago": ["US"],
            "Europe/London": ["GB"],
            "Europe/Paris": ["FR"],
            "Asia/Shanghai": ["CN"],
            "Asia/Tokyo": ["JP"],
            "Asia/Seoul": ["KR"],
            "Australia/Sydney": ["AU"]
        }
        
        if timezone in timezone_country_map:
            return country_code in timezone_country_map[timezone]
        
        # 通过时区字符串推断
        if "/" in timezone:
            region = timezone.split("/")[0]
            region_countries = {
                "America": ["US", "CA", "MX", "BR", "AR"],
                "Europe": ["GB", "FR", "DE", "IT", "ES"],
                "Asia": ["CN", "JP", "KR", "IN", "SG"],
                "Australia": ["AU"],
                "Africa": ["ZA", "EG", "NG"]
            }
            if region in region_countries:
                return country_code in region_countries[region]
        
        return True
    
    def _calculate_uniqueness(self, data: Dict[str, Any]) -> float:
        """计算指纹唯一性（越高越容易被追踪）"""
        uniqueness = 0.0
        
        # Canvas指纹存在
        if data.get("canvas_fingerprint"):
            uniqueness += 30
        
        # WebGL指纹存在
        if data.get("webgl_fingerprint"):
            uniqueness += 25
        
        # 字体列表很长
        fonts_count = len(data.get("fonts", []))
        if fonts_count > 20:
            uniqueness += 15
        elif fonts_count > 10:
            uniqueness += 10
        
        # 插件列表
        plugins_count = len(data.get("plugins", []))
        if plugins_count > 0:
            uniqueness += 10
        
        # 非常见分辨率
        resolution = data.get("screen_resolution", "")
        if resolution not in self.COMMON_RESOLUTIONS:
            uniqueness += 10
        
        # 罕见时区
        timezone = data.get("timezone", "")
        if timezone not in self.COMMON_TIMEZONES:
            uniqueness += 10
        
        return min(100, uniqueness)
    
    def _calculate_risk_score(
        self,
        consistency: FingerprintConsistency,
        uniqueness: float
    ) -> float:
        """计算指纹风险分数"""
        # 一致性占70%权重，唯一性占30%权重
        # 注意：唯一性高是风险，所以要反转
        consistency_score = consistency.overall_consistency
        uniqueness_risk = 100 - uniqueness  # 唯一性越高，风险越大
        
        risk_score = consistency_score * 0.7 + uniqueness_risk * 0.3
        
        return max(0, min(100, risk_score))
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """获取风险等级"""
        if score >= 80:
            return RiskLevel.LOW
        elif score >= 60:
            return RiskLevel.MEDIUM
        elif score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _identify_issues(
        self,
        basic: BasicFingerprint,
        consistency: FingerprintConsistency
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        if not consistency.os_ua_match:
            issues.append("操作系统与User-Agent不匹配")
        
        if not consistency.resolution_device_match:
            issues.append("屏幕分辨率与设备类型不匹配")
        
        if not consistency.language_location_match:
            issues.append("浏览器语言与IP地理位置不匹配")
        
        if not consistency.timezone_location_match:
            issues.append("时区设置与IP地理位置不匹配")
        
        if consistency.overall_consistency < 50:
            issues.append("整体指纹一致性较差，容易被识别")
        
        return issues
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "操作系统" in issue:
                recommendations.append("确保User-Agent与实际操作系统匹配")
            
            if "分辨率" in issue:
                recommendations.append("设置与设备类型相符的屏幕分辨率")
            
            if "语言" in issue:
                recommendations.append("设置浏览器语言与目标地区一致")
            
            if "时区" in issue:
                recommendations.append("设置时区与IP地理位置一致")
            
            if "一致性" in issue:
                recommendations.append("使用浏览器指纹修改工具统一配置")
        
        if not recommendations:
            recommendations.append("指纹配置良好，保持当前设置")
        
        return recommendations


# 全局服务实例
fingerprint_service = FingerprintService()
