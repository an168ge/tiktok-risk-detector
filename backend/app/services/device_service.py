"""
设备检测服务
"""
import logging
from typing import Dict, Any
from user_agents import parse as parse_user_agent

from app.schemas import (
    DeviceInfo, EmulatorDetection, DeviceDetectionResult, RiskLevel
)

logger = logging.getLogger(__name__)


class DeviceDetectionService:
    """设备检测服务"""
    
    # 模拟器特征关键词
    EMULATOR_KEYWORDS = [
        "emulator", "simulator", "virtual", "android sdk",
        "genymotion", "bluestacks", "noxplayer", "memu",
        "vbox", "vmware", "qemu"
    ]
    
    # 无头浏览器特征
    HEADLESS_KEYWORDS = [
        "headless", "phantom", "selenium", "webdriver",
        "puppeteer", "playwright"
    ]
    
    def __init__(self):
        pass
    
    async def detect_full(
        self,
        user_agent: str,
        platform: str,
        data: Dict[str, Any]
    ) -> DeviceDetectionResult:
        """完整设备检测"""
        
        # 解析设备信息
        device_info = self._parse_device_info(user_agent, platform)
        
        # 检测模拟器
        emulator_detection = self._detect_emulator(user_agent, platform, data)
        
        # 计算一致性分数
        consistency_score = self._calculate_consistency(
            user_agent,
            platform,
            device_info,
            data
        )
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(
            emulator_detection,
            consistency_score
        )
        risk_level = self._get_risk_level(risk_score)
        
        # 识别问题
        issues = self._identify_issues(
            device_info,
            emulator_detection,
            consistency_score
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return DeviceDetectionResult(
            device=device_info,
            emulator=emulator_detection,
            consistency_score=consistency_score,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
    
    def _parse_device_info(self, user_agent: str, platform: str) -> DeviceInfo:
        """解析设备信息"""
        ua = parse_user_agent(user_agent)
        
        # 判断设备类型
        if ua.is_mobile:
            if ua.is_tablet:
                device_type = "tablet"
            else:
                device_type = "mobile"
        else:
            device_type = "desktop"
        
        return DeviceInfo(
            device_type=device_type,
            os=ua.os.family,
            os_version=ua.os.version_string,
            browser=ua.browser.family,
            browser_version=ua.browser.version_string,
            is_mobile=ua.is_mobile,
            is_tablet=ua.is_tablet,
            is_desktop=not ua.is_mobile
        )
    
    def _detect_emulator(
        self,
        user_agent: str,
        platform: str,
        data: Dict[str, Any]
    ) -> EmulatorDetection:
        """检测模拟器"""
        
        is_emulator = False
        is_virtual_machine = False
        is_headless_browser = False
        confidence = 0.0
        detected_patterns = []
        
        # 检查User-Agent中的模拟器关键词
        ua_lower = user_agent.lower()
        for keyword in self.EMULATOR_KEYWORDS:
            if keyword in ua_lower:
                is_emulator = True
                confidence += 30
                detected_patterns.append(f"UA包含模拟器关键词: {keyword}")
        
        # 检查无头浏览器特征
        for keyword in self.HEADLESS_KEYWORDS:
            if keyword in ua_lower:
                is_headless_browser = True
                confidence += 40
                detected_patterns.append(f"UA包含无头浏览器关键词: {keyword}")
        
        # 检查平台信息
        platform_lower = platform.lower()
        for keyword in self.EMULATOR_KEYWORDS:
            if keyword in platform_lower:
                is_emulator = True
                confidence += 25
                detected_patterns.append(f"Platform包含模拟器关键词: {keyword}")
        
        # 检查硬件特征异常
        hardware_concurrency = data.get("hardware_concurrency")
        device_memory = data.get("device_memory")
        max_touch_points = data.get("max_touch_points", 0)
        
        # 移动设备但没有触摸点
        if data.get("is_mobile") and max_touch_points == 0:
            is_emulator = True
            confidence += 20
            detected_patterns.append("移动设备但无触摸点")
        
        # CPU核心数异常（模拟器常见值）
        if hardware_concurrency in [1, 2]:
            confidence += 10
            detected_patterns.append(f"CPU核心数异常: {hardware_concurrency}")
        
        # 设备内存异常
        if device_memory and device_memory < 2:
            confidence += 10
            detected_patterns.append(f"设备内存过低: {device_memory}GB")
        
        # 检查WebDriver标志
        if data.get("has_webdriver"):
            is_headless_browser = True
            confidence += 50
            detected_patterns.append("检测到WebDriver标志")
        
        # 检查虚拟机特征
        if "vbox" in ua_lower or "vmware" in ua_lower:
            is_virtual_machine = True
            confidence += 30
            detected_patterns.append("检测到虚拟机特征")
        
        # 限制置信度在0-100之间
        confidence = min(100, confidence)
        
        return EmulatorDetection(
            is_emulator=is_emulator,
            is_virtual_machine=is_virtual_machine,
            is_headless_browser=is_headless_browser,
            confidence=confidence,
            detected_patterns=detected_patterns
        )
    
    def _calculate_consistency(
        self,
        user_agent: str,
        platform: str,
        device_info: DeviceInfo,
        data: Dict[str, Any]
    ) -> float:
        """计算设备信息一致性"""
        
        consistency_score = 100.0
        
        # 检查触摸点数与设备类型的一致性
        max_touch_points = data.get("max_touch_points", 0)
        if device_info.is_mobile and max_touch_points == 0:
            consistency_score -= 30
        elif device_info.is_desktop and max_touch_points > 0:
            consistency_score -= 20
        
        # 检查屏幕分辨率与设备类型的一致性
        screen_resolution = data.get("screen_resolution", "")
        if screen_resolution:
            try:
                width, height = map(int, screen_resolution.split("x"))
                max_dimension = max(width, height)
                
                if device_info.is_mobile and max_dimension > 500:
                    consistency_score -= 15
                elif device_info.is_desktop and max_dimension < 1000:
                    consistency_score -= 15
            except (ValueError, AttributeError):
                pass
        
        # 检查硬件并发数的合理性
        hardware_concurrency = data.get("hardware_concurrency")
        if hardware_concurrency:
            if hardware_concurrency < 2:
                consistency_score -= 10
            elif hardware_concurrency > 16:
                consistency_score -= 5
        
        return max(0, min(100, consistency_score))
    
    def _calculate_risk_score(
        self,
        emulator: EmulatorDetection,
        consistency_score: float
    ) -> float:
        """计算设备风险分数"""
        
        score = consistency_score
        
        # 如果检测到模拟器，大幅降低分数
        if emulator.is_emulator:
            score -= emulator.confidence * 0.5
        
        if emulator.is_headless_browser:
            score -= 40
        
        if emulator.is_virtual_machine:
            score -= 25
        
        return max(0, min(100, score))
    
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
        device_info: DeviceInfo,
        emulator: EmulatorDetection,
        consistency_score: float
    ) -> list[str]:
        """识别问题"""
        issues = []
        
        if emulator.is_emulator:
            issues.append(
                f"检测到模拟器特征（置信度{emulator.confidence:.0f}%）"
            )
            if emulator.detected_patterns:
                for pattern in emulator.detected_patterns[:3]:  # 只显示前3个
                    issues.append(f"  - {pattern}")
        
        if emulator.is_headless_browser:
            issues.append("检测到无头浏览器（自动化工具）")
        
        if emulator.is_virtual_machine:
            issues.append("检测到虚拟机环境")
        
        if consistency_score < 70:
            issues.append("设备信息一致性较差")
        
        return issues
    
    def _generate_recommendations(self, issues: list[str]) -> list[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "模拟器" in issue:
                recommendations.append("使用真实设备访问TikTok")
                recommendations.append("如必须使用模拟器，选择高质量的设备模拟工具")
            
            if "无头浏览器" in issue:
                recommendations.append("避免使用自动化工具访问TikTok")
                recommendations.append("使用正常的浏览器环境")
            
            if "虚拟机" in issue:
                recommendations.append("避免在虚拟机中访问TikTok")
                recommendations.append("使用物理机或更好的虚拟化方案")
            
            if "一致性" in issue:
                recommendations.append("确保设备信息配置合理且一致")
                recommendations.append("使用专业的浏览器指纹管理工具")
        
        if not recommendations:
            recommendations.append("设备配置正常，未检测到异常")
        
        return list(set(recommendations))  # 去重


# 全局服务实例
device_detection_service = DeviceDetectionService()
