"""
DNS检测服务
"""
import asyncio
import logging
from typing import List, Optional
import httpx

from app.schemas import (
    DNSServer, DNSDetectionResult, RiskLevel
)

logger = logging.getLogger(__name__)


class DNSDetectionService:
    """DNS检测服务"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        # 常见的DNS提供商
        self.known_dns_providers = {
            "8.8.8.8": "Google DNS",
            "8.8.4.4": "Google DNS",
            "1.1.1.1": "Cloudflare DNS",
            "1.0.0.1": "Cloudflare DNS",
            "9.9.9.9": "Quad9 DNS",
            "208.67.222.222": "OpenDNS",
            "208.67.220.220": "OpenDNS",
        }
    
    async def detect_full(
        self,
        dns_servers: List[str],
        expected_country: Optional[str] = None,
        vpn_ip: Optional[str] = None
    ) -> DNSDetectionResult:
        """完整DNS检测"""
        
        # 解析DNS服务器信息
        dns_server_list = await self._parse_dns_servers(dns_servers)
        
        # 检测DNS泄露
        leak_detected, leak_severity, vpn_dns_match = await self._check_dns_leak(
            dns_server_list,
            expected_country,
            vpn_ip
        )
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(
            leak_detected,
            leak_severity,
            vpn_dns_match
        )
        risk_level = self._get_risk_level(risk_score)
        
        # 识别问题
        issues = self._identify_issues(
            leak_detected,
            leak_severity,
            vpn_dns_match,
            dns_server_list
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return DNSDetectionResult(
            dns_servers=dns_server_list,
            leak_detected=leak_detected,
            leak_severity=leak_severity,
            vpn_dns_match=vpn_dns_match,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
    
    async def _parse_dns_servers(self, dns_ips: List[str]) -> List[DNSServer]:
        """解析DNS服务器信息"""
        dns_servers = []
        
        for dns_ip in dns_ips:
            # 检查是否是已知的DNS提供商
            provider = self.known_dns_providers.get(dns_ip, "Unknown")
            
            # 获取DNS服务器的地理位置
            location = await self._get_dns_location(dns_ip)
            
            dns_servers.append(DNSServer(
                ip=dns_ip,
                location=location,
                provider=provider
            ))
        
        return dns_servers
    
    async def _get_dns_location(self, dns_ip: str) -> Optional[str]:
        """获取DNS服务器地理位置"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"http://ip-api.com/json/{dns_ip}",
                    params={"fields": "country,city"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("country"):
                        city = data.get("city", "")
                        return f"{data['country']}, {city}" if city else data['country']
        
        except Exception as e:
            logger.error(f"Failed to get DNS location: {e}")
        
        return None
    
    async def _check_dns_leak(
        self,
        dns_servers: List[DNSServer],
        expected_country: Optional[str],
        vpn_ip: Optional[str]
    ) -> tuple[bool, str, bool]:
        """检测DNS泄露"""
        
        if not dns_servers:
            return False, "none", True
        
        leak_detected = False
        leak_severity = "none"
        vpn_dns_match = True
        
        # 如果使用VPN，检查DNS是否也来自VPN
        if vpn_ip:
            # 检查是否有DNS服务器不在VPN网络中
            non_vpn_dns = []
            for dns in dns_servers:
                # 如果DNS是常见的公共DNS，可能不是VPN提供的
                if dns.provider in ["Google DNS", "Cloudflare DNS", "OpenDNS"]:
                    non_vpn_dns.append(dns)
                # 如果DNS位置与VPN IP位置不同
                elif dns.location and expected_country:
                    if expected_country not in dns.location:
                        non_vpn_dns.append(dns)
            
            if non_vpn_dns:
                leak_detected = True
                vpn_dns_match = False
                
                # 根据泄露的DNS数量判断严重程度
                leak_ratio = len(non_vpn_dns) / len(dns_servers)
                if leak_ratio >= 0.8:
                    leak_severity = "high"
                elif leak_ratio >= 0.5:
                    leak_severity = "medium"
                else:
                    leak_severity = "low"
        
        # 如果期望的国家与DNS位置不匹配
        if expected_country:
            mismatched_dns = [
                dns for dns in dns_servers
                if dns.location and expected_country not in dns.location
            ]
            
            if mismatched_dns and len(mismatched_dns) >= len(dns_servers) * 0.5:
                leak_detected = True
                if leak_severity == "none":
                    leak_severity = "medium"
        
        return leak_detected, leak_severity, vpn_dns_match
    
    def _calculate_risk_score(
        self,
        leak_detected: bool,
        leak_severity: str,
        vpn_dns_match: bool
    ) -> float:
        """计算DNS风险分数"""
        score = 100.0
        
        if leak_detected:
            # 根据泄露严重程度扣分
            if leak_severity == "high":
                score -= 50
            elif leak_severity == "medium":
                score -= 30
            elif leak_severity == "low":
                score -= 15
        
        if not vpn_dns_match:
            score -= 20
        
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
        vpn_dns_match: bool,
        dns_servers: List[DNSServer]
    ) -> List[str]:
        """识别问题"""
        issues = []
        
        if leak_detected:
            if leak_severity == "high":
                issues.append("检测到严重的DNS泄露，真实位置可能完全暴露")
            elif leak_severity == "medium":
                issues.append("检测到中等程度的DNS泄露")
            elif leak_severity == "low":
                issues.append("检测到轻微的DNS泄露")
        
        if not vpn_dns_match:
            issues.append("DNS服务器不是VPN提供的，使用了ISP的DNS")
        
        # 检查是否使用了公共DNS
        public_dns_count = sum(
            1 for dns in dns_servers
            if dns.provider in ["Google DNS", "Cloudflare DNS", "OpenDNS"]
        )
        if public_dns_count == len(dns_servers):
            issues.append("使用公共DNS而非VPN DNS，可能导致隐私泄露")
        
        return issues
    
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "DNS泄露" in issue:
                recommendations.append("在VPN设置中启用DNS泄露保护功能")
                recommendations.append("手动配置DNS服务器为VPN提供的DNS")
            
            if "ISP的DNS" in issue or "公共DNS" in issue:
                recommendations.append("修改系统DNS设置为VPN提供的DNS服务器")
                recommendations.append("检查VPN软件的DNS劫持功能是否启用")
        
        if not recommendations:
            recommendations.append("DNS配置良好，未检测到泄露")
        
        return recommendations


# 全局服务实例
dns_detection_service = DNSDetectionService()
