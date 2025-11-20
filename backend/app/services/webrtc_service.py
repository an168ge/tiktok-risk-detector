"""
WebRTC检测服务
"""
import logging
from typing import List
import ipaddress

from app.schemas import (
    WebRTCDetectionResult, RiskLevel
)

logger = logging.getLogger(__name__)


class WebRTCDetectionService:
    """WebRTC检测服务"""
    
    def __init__(self):
        # 本地IP范围
        self.local_ip_ranges = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("127.0.0.0/8"),
        ]
    
    async def detect_full(
        self,
        webrtc_ips: List[str],
        vpn_ip: str,
        real_ip: str = None
    ) -> WebRTCDetectionResult:
        """完整WebRTC检测"""
        
        # 分类IP地址
        local_ips, public_ips = self._classify_ips(webrtc_ips)
        
        # 检测泄露
        leak_detected, leak_severity, real_ip_exposed = self._check_webrtc_leak(
            local_ips,
            public_ips,
            vpn_ip,
            real_ip
        )
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(
            leak_detected,
            leak_severity,
            real_ip_exposed
        )
        risk_level = self._get_risk_level(risk_score)
        
        # 识别问题
        issues = self._identify_issues(
            leak_detected,
            leak_severity,
            real_ip_exposed,
            local_ips,
            public_ips
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return WebRTCDetectionResult(
            local_ips=local_ips,
            public_ips=public_ips,
            leak_detected=leak_detected,
            leak_severity=leak_severity,
            real_ip_exposed=real_ip_exposed,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
    
    def _classify_ips(self, ips: List[str]) -> tuple[List[str], List[str]]:
        """分类IP地址为本地IP和公网IP"""
        local_ips = []
        public_ips = []
        
        for ip_str in ips:
            try:
                ip = ipaddress.ip_address(ip_str)
                
                # 检查是否是本地IP
                is_local = any(
                    ip in network
                    for network in self.local_ip_ranges
                )
                
                if is_local or ip.is_private:
                    local_ips.append(ip_str)
                else:
                    public_ips.append(ip_str)
            
            except ValueError:
                logger.warning(f"Invalid IP address: {ip_str}")
                continue
        
        return local_ips, public_ips
    
    def _check_webrtc_leak(
        self,
        local_ips: List[str],
        public_ips: List[str],
        vpn_ip: str,
        real_ip: str = None
    ) -> tuple[bool, str, bool]:
        """检测WebRTC泄露"""
        
        leak_detected = False
        leak_severity = "none"
        real_ip_exposed = False
        
        # 如果暴露了公网IP
        if public_ips:
            leak_detected = True
            
            # 检查是否暴露了真实IP
            if real_ip and real_ip in public_ips:
                real_ip_exposed = True
                leak_severity = "high"
            else:
                # 检查公网IP是否与VPN IP不同
                if vpn_ip not in public_ips:
                    leak_severity = "high"
                    real_ip_exposed = True
                else:
                    # 只暴露了VPN IP，风险较低
                    leak_severity = "low"
        
        # 如果只暴露了本地IP
        elif local_ips:
            leak_detected = True
            leak_severity = "low"
        
        return leak_detected, leak_severity, real_ip_exposed
    
    def _calculate_risk_score(
        self,
        leak_detected: bool,
        leak_severity: str,
        real_ip_exposed: bool
    ) -> float:
        """计算WebRTC风险分数"""
        score = 100.0
        
        if leak_detected:
            if leak_severity == "high":
                score -= 60
            elif leak_severity == "medium":
                score -= 35
            elif leak_severity == "low":
                score -= 15
        
        if real_ip_exposed:
            score -= 30
        
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
        leak_detected: bool,
        leak_severity: str,
        real_ip_exposed: bool,
        local_ips: List[str],
        public_ips: List[str]
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        if real_ip_exposed:
            issues.append("WebRTC泄露了真实公网IP地址，严重威胁隐私")
        
        if leak_detected:
            if leak_severity == "high":
                if not real_ip_exposed:
                    issues.append("WebRTC泄露了公网IP地址")
            elif leak_severity == "medium":
                issues.append("WebRTC泄露了部分网络信息")
            elif leak_severity == "low":
                issues.append("WebRTC泄露了本地IP地址")
        
        if public_ips:
            issues.append(f"检测到{len(public_ips)}个公网IP地址泄露")
        
        if local_ips and len(local_ips) > 3:
            issues.append(f"检测到过多的本地IP地址({len(local_ips)}个)")
        
        return issues
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "真实公网IP" in issue or "公网IP" in issue:
                recommendations.append("在浏览器中完全禁用WebRTC功能")
                recommendations.append("安装WebRTC泄露防护插件（如uBlock Origin）")
                recommendations.append("使用支持WebRTC保护的浏览器扩展")
            
            if "本地IP" in issue:
                recommendations.append("配置浏览器隐藏本地IP地址")
                recommendations.append("使用浏览器的隐私保护模式")
        
        if not recommendations:
            recommendations.append("WebRTC配置安全，未检测到IP泄露")
        
        return recommendations


# 全局服务实例
webrtc_detection_service = WebRTCDetectionService()
