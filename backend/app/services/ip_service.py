"""
IP检测服务
"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.schemas import (
    IPInfo, IPQuality, IPDetectionResult, IPType, RiskLevel
)
from app.config import settings
from app.core.cache import redis_client

logger = logging.getLogger(__name__)


class IPDetectionService:
    """IP检测服务"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        self.cache_ttl = 3600  # IP检测结果缓存1小时
    
    async def detect_full(self, ip: str) -> IPDetectionResult:
        """完整IP检测"""
        # 检查缓存
        cache_key = redis_client.make_key("ip_detection", ip)
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.info(f"IP detection cache hit: {ip}")
            return IPDetectionResult(**cached_result)
        
        # 执行检测
        info = await self.get_ip_info(ip)
        quality = await self.check_ip_quality(ip)
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(quality)
        risk_level = self._get_risk_level(risk_score)
        
        # 生成问题和建议
        issues = self._identify_issues(quality)
        recommendations = self._generate_recommendations(issues)
        
        result = IPDetectionResult(
            info=info,
            quality=quality,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
        
        # 缓存结果
        await redis_client.set(
            cache_key,
            result.model_dump(),
            ttl=self.cache_ttl
        )
        
        return result
    
    async def get_ip_info(self, ip: str) -> IPInfo:
        """获取IP基础信息"""
        try:
            # 使用ip-api.com免费API（无需密钥）
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={
                        "fields": "status,message,country,countryCode,region,city,"
                                "lat,lon,isp,as,asname,query"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        return IPInfo(
                            ip=data.get("query", ip),
                            country=data.get("country"),
                            country_code=data.get("countryCode"),
                            region=data.get("region"),
                            city=data.get("city"),
                            latitude=data.get("lat"),
                            longitude=data.get("lon"),
                            isp=data.get("isp"),
                            asn=data.get("as"),
                            as_name=data.get("asname")
                        )
        
        except Exception as e:
            logger.error(f"Failed to get IP info: {e}")
        
        # 返回默认值
        return IPInfo(ip=ip)
    
    async def check_ip_quality(self, ip: str) -> IPQuality:
        """检测IP质量"""
        # 尝试使用多个API进行检测
        
        # 方案1: 使用IPHub API（如果配置了）
        if settings.IPHUB_API_KEY:
            result = await self._check_with_iphub(ip)
            if result:
                return result
        
        # 方案2: 使用IPQualityScore API（如果配置了）
        if settings.IPQUALITYSCORE_API_KEY:
            result = await self._check_with_ipqualityscore(ip)
            if result:
                return result
        
        # 方案3: 使用免费的ipqs.io API
        result = await self._check_with_ipqs_free(ip)
        if result:
            return result
        
        # 默认返回（假设是住宅IP，无风险）
        return IPQuality(
            ip_type=IPType.RESIDENTIAL,
            is_vpn=False,
            is_proxy=False,
            is_datacenter=False,
            is_tor=False,
            is_hosting=False,
            reputation_score=80.0,
            fraud_score=20.0
        )
    
    async def _check_with_iphub(self, ip: str) -> Optional[IPQuality]:
        """使用IPHub API检测"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"https://v2.api.iphub.info/ip/{ip}",
                    headers={"X-Key": settings.IPHUB_API_KEY}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    block = data.get("block", 0)
                    
                    # IPHub的block字段: 0=住宅, 1=VPN/代理, 2=数据中心
                    is_vpn = block == 1
                    is_datacenter = block == 2
                    ip_type = IPType.RESIDENTIAL if block == 0 else (
                        IPType.VPN if is_vpn else IPType.DATACENTER
                    )
                    
                    return IPQuality(
                        ip_type=ip_type,
                        is_vpn=is_vpn,
                        is_proxy=is_vpn,
                        is_datacenter=is_datacenter,
                        reputation_score=100 - (block * 40),
                        fraud_score=block * 40
                    )
        
        except Exception as e:
            logger.error(f"IPHub API error: {e}")
        
        return None
    
    async def _check_with_ipqualityscore(self, ip: str) -> Optional[IPQuality]:
        """使用IPQualityScore API检测"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"https://ipqualityscore.com/api/json/ip/{settings.IPQUALITYSCORE_API_KEY}/{ip}",
                    params={"strictness": 1}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("success"):
                        is_vpn = data.get("vpn", False)
                        is_proxy = data.get("proxy", False)
                        is_tor = data.get("tor", False)
                        fraud_score = data.get("fraud_score", 0)
                        
                        # 判断IP类型
                        if is_vpn:
                            ip_type = IPType.VPN
                        elif is_proxy:
                            ip_type = IPType.PROXY
                        elif is_tor:
                            ip_type = IPType.PROXY
                        else:
                            ip_type = IPType.RESIDENTIAL
                        
                        return IPQuality(
                            ip_type=ip_type,
                            is_vpn=is_vpn,
                            is_proxy=is_proxy,
                            is_datacenter=data.get("is_crawler", False),
                            is_tor=is_tor,
                            reputation_score=100 - fraud_score,
                            fraud_score=fraud_score,
                            abuse_confidence_score=data.get("abuse_velocity", 0)
                        )
        
        except Exception as e:
            logger.error(f"IPQualityScore API error: {e}")
        
        return None
    
    async def _check_with_ipqs_free(self, ip: str) -> Optional[IPQuality]:
        """使用免费的proxycheck.io API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"https://proxycheck.io/v2/{ip}",
                    params={"vpn": 1, "asn": 1}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ip_data = data.get(ip, {})
                    
                    if ip_data:
                        is_proxy = ip_data.get("proxy", "no") == "yes"
                        proxy_type = ip_data.get("type", "").lower()
                        
                        is_vpn = "vpn" in proxy_type
                        is_datacenter = "hosting" in proxy_type or "datacenter" in proxy_type
                        
                        if is_vpn:
                            ip_type = IPType.VPN
                        elif is_proxy:
                            ip_type = IPType.PROXY
                        elif is_datacenter:
                            ip_type = IPType.DATACENTER
                        else:
                            ip_type = IPType.RESIDENTIAL
                        
                        fraud_score = 50.0 if is_proxy else 10.0
                        
                        return IPQuality(
                            ip_type=ip_type,
                            is_vpn=is_vpn,
                            is_proxy=is_proxy,
                            is_datacenter=is_datacenter,
                            reputation_score=100 - fraud_score,
                            fraud_score=fraud_score
                        )
        
        except Exception as e:
            logger.error(f"Proxycheck.io API error: {e}")
        
        return None
    
    def _calculate_risk_score(self, quality: IPQuality) -> float:
        """计算IP风险分数（0-100，越高越好）"""
        score = 100.0
        
        # VPN扣分
        if quality.is_vpn:
            score -= 30
        
        # 代理扣分
        if quality.is_proxy:
            score -= 25
        
        # 数据中心扣分
        if quality.is_datacenter:
            score -= 20
        
        # Tor扣分
        if quality.is_tor:
            score -= 40
        
        # 托管IP扣分
        if quality.is_hosting:
            score -= 15
        
        # 基于信誉分数调整
        reputation_factor = quality.reputation_score / 100
        score = score * 0.7 + quality.reputation_score * 0.3
        
        return max(0, min(100, score))
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """根据分数获取风险等级"""
        if score >= 80:
            return RiskLevel.LOW
        elif score >= 60:
            return RiskLevel.MEDIUM
        elif score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _identify_issues(self, quality: IPQuality) -> list[str]:
        """识别问题"""
        issues = []
        
        if quality.is_vpn:
            issues.append("检测到VPN连接，可能被TikTok识别")
        
        if quality.is_proxy:
            issues.append("检测到代理服务器，风险较高")
        
        if quality.is_datacenter:
            issues.append("IP来自数据中心，不是住宅IP")
        
        if quality.is_tor:
            issues.append("检测到Tor网络，极高风险")
        
        if quality.fraud_score > 50:
            issues.append(f"IP欺诈分数较高 ({quality.fraud_score:.1f}/100)")
        
        if quality.reputation_score < 50:
            issues.append(f"IP信誉分数较低 ({quality.reputation_score:.1f}/100)")
        
        return issues
    
    def _generate_recommendations(self, issues: list[str]) -> list[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "VPN" in issue:
                recommendations.append("建议更换为住宅IP的VPN提供商")
            
            if "代理" in issue:
                recommendations.append("避免使用免费或公共代理服务")
            
            if "数据中心" in issue:
                recommendations.append("使用住宅IP或4G/5G移动网络")
            
            if "Tor" in issue:
                recommendations.append("不建议使用Tor访问TikTok")
            
            if "欺诈分数" in issue or "信誉" in issue:
                recommendations.append("更换IP地址或VPN节点")
        
        if not recommendations:
            recommendations.append("当前IP质量良好，继续保持")
        
        return recommendations


# 全局服务实例
ip_detection_service = IPDetectionService()
