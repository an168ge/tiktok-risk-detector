"""
网络质量和TikTok连接检测服务
"""
import asyncio
import time
import logging
from typing import Optional
import httpx

from app.schemas import (
    NetworkQuality, TikTokConnectivity, NetworkDetectionResult, RiskLevel
)
from app.config import settings

logger = logging.getLogger(__name__)


class NetworkDetectionService:
    """网络质量和TikTok检测服务"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(15.0)
        self.tiktok_domains = [
            "https://www.tiktok.com",
            "https://m.tiktok.com",
        ]
        self.tiktok_cdn_domains = settings.TIKTOK_CDN_DOMAINS
    
    async def detect_full(self) -> NetworkDetectionResult:
        """完整网络检测"""
        
        # 测试TikTok连接性
        tiktok_connectivity = await self._test_tiktok_connectivity()
        
        # 测试网络质量（简化版）
        network_quality = await self._test_network_quality()
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(
            tiktok_connectivity,
            network_quality
        )
        risk_level = self._get_risk_level(risk_score)
        
        # 识别问题
        issues = self._identify_issues(tiktok_connectivity, network_quality)
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return NetworkDetectionResult(
            quality=network_quality,
            tiktok_connectivity=tiktok_connectivity,
            risk_score=risk_score,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations
        )
    
    async def _test_tiktok_connectivity(self) -> TikTokConnectivity:
        """测试TikTok连接性"""
        
        main_domain_accessible = False
        cdn_accessible = False
        api_accessible = False
        latencies = []
        connection_stable = True
        
        # 测试主域名
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for domain in self.tiktok_domains:
                try:
                    start_time = time.time()
                    response = await client.get(domain)
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status_code in [200, 301, 302, 403]:
                        main_domain_accessible = True
                        latencies.append(latency)
                        logger.info(f"TikTok domain accessible: {domain}, latency: {latency:.0f}ms")
                        break
                
                except Exception as e:
                    logger.warning(f"Failed to access {domain}: {e}")
                    continue
        
        # 测试CDN（简化版，只测试一个）
        if self.tiktok_cdn_domains:
            cdn_domain = f"https://{self.tiktok_cdn_domains[0]}"
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    start_time = time.time()
                    response = await client.get(cdn_domain)
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status_code in [200, 301, 302, 403, 404]:
                        cdn_accessible = True
                        latencies.append(latency)
            
            except Exception as e:
                logger.warning(f"Failed to access CDN: {e}")
        
        # 计算平均延迟
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        # 判断连接稳定性
        if latencies and len(latencies) > 1:
            # 计算延迟标准差（简化版）
            avg = sum(latencies) / len(latencies)
            variance = sum((x - avg) ** 2 for x in latencies) / len(latencies)
            std_dev = variance ** 0.5
            
            # 如果标准差过大，认为不稳定
            if std_dev > avg * 0.5:
                connection_stable = False
        
        return TikTokConnectivity(
            main_domain_accessible=main_domain_accessible,
            cdn_accessible=cdn_accessible,
            api_accessible=api_accessible,  # 暂不测试API
            avg_latency_ms=avg_latency,
            connection_stable=connection_stable
        )
    
    async def _test_network_quality(self) -> NetworkQuality:
        """测试网络质量（简化版）"""
        
        # 测试到多个服务器的延迟
        test_urls = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.amazon.com"
        ]
        
        latencies = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in test_urls:
                try:
                    start_time = time.time()
                    await client.get(url)
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                except Exception:
                    continue
        
        # 计算平均延迟
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        # 计算抖动（简化版）
        jitter = None
        if len(latencies) > 1:
            diffs = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
            jitter = sum(diffs) / len(diffs)
        
        return NetworkQuality(
            latency_ms=avg_latency,
            jitter_ms=jitter,
            packet_loss=None,  # 简化版不测试丢包
            download_speed_mbps=None,  # 简化版不测试速度
            upload_speed_mbps=None
        )
    
    def _calculate_risk_score(
        self,
        tiktok: TikTokConnectivity,
        quality: NetworkQuality
    ) -> float:
        """计算网络风险分数"""
        
        score = 100.0
        
        # TikTok连接性检查
        if not tiktok.main_domain_accessible:
            score -= 60
        
        if not tiktok.cdn_accessible:
            score -= 20
        
        if not tiktok.connection_stable:
            score -= 10
        
        # 延迟检查
        if tiktok.avg_latency_ms:
            if tiktok.avg_latency_ms > 1000:
                score -= 20
            elif tiktok.avg_latency_ms > 500:
                score -= 10
            elif tiktok.avg_latency_ms > 300:
                score -= 5
        
        # 网络质量检查
        if quality.jitter_ms and quality.jitter_ms > 50:
            score -= 10
        
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
        tiktok: TikTokConnectivity,
        quality: NetworkQuality
    ) -> list[str]:
        """识别问题"""
        issues = []
        
        if not tiktok.main_domain_accessible:
            issues.append("无法访问TikTok主域名，VPN可能被封锁")
        
        if not tiktok.cdn_accessible:
            issues.append("无法访问TikTok CDN，视频加载可能受影响")
        
        if not tiktok.connection_stable:
            issues.append("网络连接不稳定，可能影响使用体验")
        
        if tiktok.avg_latency_ms:
            if tiktok.avg_latency_ms > 1000:
                issues.append(f"访问延迟过高（{tiktok.avg_latency_ms:.0f}ms），体验极差")
            elif tiktok.avg_latency_ms > 500:
                issues.append(f"访问延迟较高（{tiktok.avg_latency_ms:.0f}ms），可能卡顿")
        
        if quality.jitter_ms and quality.jitter_ms > 50:
            issues.append(f"网络抖动较大（{quality.jitter_ms:.0f}ms），连接不稳定")
        
        return issues
    
    def _generate_recommendations(self, issues: list[str]) -> list[str]:
        """生成修复建议"""
        recommendations = []
        
        for issue in issues:
            if "无法访问TikTok" in issue or "被封锁" in issue:
                recommendations.append("更换VPN节点或服务商")
                recommendations.append("尝试不同的VPN协议（如WireGuard、OpenVPN）")
                recommendations.append("检查VPN是否支持访问TikTok")
            
            if "延迟" in issue:
                recommendations.append("选择地理位置更近的VPN节点")
                recommendations.append("使用有线网络代替Wi-Fi")
                recommendations.append("检查本地网络连接质量")
            
            if "不稳定" in issue or "抖动" in issue:
                recommendations.append("检查网络连接是否稳定")
                recommendations.append("关闭其他占用带宽的应用")
                recommendations.append("考虑升级网络带宽")
        
        if not recommendations:
            recommendations.append("网络连接良好，TikTok访问正常")
        
        return list(set(recommendations))  # 去重


# 全局服务实例
network_detection_service = NetworkDetectionService()
