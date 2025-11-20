"""
风险评分引擎
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.schemas import (
    DetectionReport, RiskScoreBreakdown, Recommendation,
    RiskLevel, DetectionStatus,
    IPDetectionResult, DNSDetectionResult, WebRTCDetectionResult,
    FingerprintDetectionResult, DeviceDetectionResult, NetworkDetectionResult
)
from app.config import settings

logger = logging.getLogger(__name__)


class RiskScoringService:
    """风险评分引擎"""
    
    def __init__(self):
        # 各模块权重（从配置文件读取）
        self.weights = {
            "ip": settings.RISK_WEIGHT_IP,
            "privacy": settings.RISK_WEIGHT_PRIVACY,
            "fingerprint": settings.RISK_WEIGHT_FINGERPRINT,
            "device": settings.RISK_WEIGHT_DEVICE,
            "network": settings.RISK_WEIGHT_NETWORK
        }
    
    async def generate_report(
        self,
        detection_id: Optional[str] = None,
        ip_result: Optional[IPDetectionResult] = None,
        dns_result: Optional[DNSDetectionResult] = None,
        webrtc_result: Optional[WebRTCDetectionResult] = None,
        fingerprint_result: Optional[FingerprintDetectionResult] = None,
        device_result: Optional[DeviceDetectionResult] = None,
        network_result: Optional[NetworkDetectionResult] = None
    ) -> DetectionReport:
        """生成完整检测报告"""
        
        if not detection_id:
            detection_id = str(uuid.uuid4())
        
        # 计算各模块分数
        score_breakdown = self._calculate_score_breakdown(
            ip_result, dns_result, webrtc_result,
            fingerprint_result, device_result, network_result
        )
        
        # 计算总分
        overall_score = self._calculate_overall_score(score_breakdown)
        
        # 确定总体风险等级
        overall_risk_level = self._get_risk_level(overall_score)
        
        # 收集所有问题
        all_issues = self._collect_all_issues(
            ip_result, dns_result, webrtc_result,
            fingerprint_result, device_result, network_result
        )
        
        # 生成修复建议
        recommendations = self._generate_recommendations(
            all_issues, ip_result, dns_result, webrtc_result,
            fingerprint_result, device_result, network_result
        )
        
        return DetectionReport(
            detection_id=detection_id,
            timestamp=datetime.utcnow(),
            status=DetectionStatus.COMPLETED,
            ip_result=ip_result,
            dns_result=dns_result,
            webrtc_result=webrtc_result,
            fingerprint_result=fingerprint_result,
            device_result=device_result,
            network_result=network_result,
            overall_score=overall_score,
            overall_risk_level=overall_risk_level,
            score_breakdown=score_breakdown,
            all_issues=all_issues,
            recommendations=recommendations
        )
    
    def _calculate_score_breakdown(
        self,
        ip_result: Optional[IPDetectionResult],
        dns_result: Optional[DNSDetectionResult],
        webrtc_result: Optional[WebRTCDetectionResult],
        fingerprint_result: Optional[FingerprintDetectionResult],
        device_result: Optional[DeviceDetectionResult],
        network_result: Optional[NetworkDetectionResult]
    ) -> RiskScoreBreakdown:
        """计算各模块分数"""
        
        # IP分数
        ip_score = ip_result.risk_score if ip_result else 50.0
        
        # 隐私分数（DNS + WebRTC）
        privacy_scores = []
        if dns_result:
            privacy_scores.append(dns_result.risk_score)
        if webrtc_result:
            privacy_scores.append(webrtc_result.risk_score)
        privacy_score = sum(privacy_scores) / len(privacy_scores) if privacy_scores else 50.0
        
        # 指纹分数
        fingerprint_score = fingerprint_result.risk_score if fingerprint_result else 50.0
        
        # 设备分数
        device_score = device_result.risk_score if device_result else 50.0
        
        # 网络分数
        network_score = network_result.risk_score if network_result else 50.0
        
        return RiskScoreBreakdown(
            ip_score=ip_score,
            privacy_score=privacy_score,
            fingerprint_score=fingerprint_score,
            device_score=device_score,
            network_score=network_score
        )
    
    def _calculate_overall_score(self, breakdown: RiskScoreBreakdown) -> float:
        """计算总体风险分数"""
        weighted_score = (
            breakdown.ip_score * self.weights["ip"] +
            breakdown.privacy_score * self.weights["privacy"] +
            breakdown.fingerprint_score * self.weights["fingerprint"] +
            breakdown.device_score * self.weights["device"] +
            breakdown.network_score * self.weights["network"]
        )
        
        return round(weighted_score, 2)
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """根据分数确定风险等级"""
        if score >= 80:
            return RiskLevel.LOW
        elif score >= 60:
            return RiskLevel.MEDIUM
        elif score >= 40:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _collect_all_issues(
        self,
        ip_result: Optional[IPDetectionResult],
        dns_result: Optional[DNSDetectionResult],
        webrtc_result: Optional[WebRTCDetectionResult],
        fingerprint_result: Optional[FingerprintDetectionResult],
        device_result: Optional[DeviceDetectionResult],
        network_result: Optional[NetworkDetectionResult]
    ) -> List[str]:
        """收集所有检测到的问题"""
        all_issues = []
        
        if ip_result and ip_result.issues:
            all_issues.extend([f"[IP] {issue}" for issue in ip_result.issues])
        
        if dns_result and dns_result.issues:
            all_issues.extend([f"[DNS] {issue}" for issue in dns_result.issues])
        
        if webrtc_result and webrtc_result.issues:
            all_issues.extend([f"[WebRTC] {issue}" for issue in webrtc_result.issues])
        
        if fingerprint_result and fingerprint_result.issues:
            all_issues.extend([f"[指纹] {issue}" for issue in fingerprint_result.issues])
        
        if device_result and device_result.issues:
            all_issues.extend([f"[设备] {issue}" for issue in device_result.issues])
        
        if network_result and network_result.issues:
            all_issues.extend([f"[网络] {issue}" for issue in network_result.issues])
        
        return all_issues
    
    def _generate_recommendations(
        self,
        all_issues: List[str],
        ip_result: Optional[IPDetectionResult],
        dns_result: Optional[DNSDetectionResult],
        webrtc_result: Optional[WebRTCDetectionResult],
        fingerprint_result: Optional[FingerprintDetectionResult],
        device_result: Optional[DeviceDetectionResult],
        network_result: Optional[NetworkDetectionResult]
    ) -> List[Recommendation]:
        """生成优先级排序的修复建议"""
        recommendations = []
        
        # IP相关建议（高优先级）
        if ip_result and ip_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            if ip_result.quality.is_vpn or ip_result.quality.is_datacenter:
                recommendations.append(Recommendation(
                    priority="critical",
                    category="ip",
                    title="更换为住宅IP",
                    description="检测到VPN或数据中心IP，TikTok很容易识别并限制访问",
                    solution="使用住宅IP的VPN服务商（如Luminati、Smartproxy），或使用4G/5G移动网络"
                ))
            
            if ip_result.quality.fraud_score > 60:
                recommendations.append(Recommendation(
                    priority="high",
                    category="ip",
                    title="IP信誉分数过低",
                    description=f"当前IP的欺诈分数为{ip_result.quality.fraud_score:.0f}/100，可能被多个平台标记",
                    solution="立即更换IP地址或VPN节点，避免使用共享IP"
                ))
        
        # DNS泄露建议（高优先级）
        if dns_result and dns_result.leak_detected:
            recommendations.append(Recommendation(
                priority="critical" if dns_result.leak_severity == "high" else "high",
                category="dns",
                title="修复DNS泄露",
                description=f"检测到{dns_result.leak_severity}程度的DNS泄露，真实位置可能暴露",
                solution="在VPN软件中启用DNS泄露保护，或手动设置DNS服务器为VPN提供的DNS"
            ))
        
        # WebRTC泄露建议（高优先级）
        if webrtc_result and webrtc_result.leak_detected:
            recommendations.append(Recommendation(
                priority="critical" if webrtc_result.real_ip_exposed else "high",
                category="webrtc",
                title="修复WebRTC泄露",
                description="WebRTC泄露了本地IP地址，可能暴露真实位置",
                solution="在浏览器中禁用WebRTC，或安装WebRTC泄露防护插件（如uBlock Origin）"
            ))
        
        # 指纹一致性建议（中优先级）
        if fingerprint_result and fingerprint_result.consistency.overall_consistency < 60:
            inconsistencies = []
            if not fingerprint_result.consistency.os_ua_match:
                inconsistencies.append("操作系统与User-Agent")
            if not fingerprint_result.consistency.timezone_location_match:
                inconsistencies.append("时区与地理位置")
            if not fingerprint_result.consistency.language_location_match:
                inconsistencies.append("语言与地理位置")
            
            recommendations.append(Recommendation(
                priority="medium",
                category="fingerprint",
                title="修复指纹不一致",
                description=f"以下项目不一致：{', '.join(inconsistencies)}",
                solution="使用浏览器指纹管理工具（如Multilogin、AdsPower）统一配置所有参数"
            ))
        
        # 设备模拟器检测建议（中优先级）
        if device_result and device_result.emulator.is_emulator:
            recommendations.append(Recommendation(
                priority="medium",
                category="device",
                title="避免使用模拟器特征",
                description=f"检测到模拟器特征（置信度{device_result.emulator.confidence:.0f}%）",
                solution="使用真实设备或更好的设备模拟工具，避免明显的模拟器标识"
            ))
        
        # 网络质量建议（低优先级）
        if network_result and network_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            if not network_result.tiktok_connectivity.main_domain_accessible:
                recommendations.append(Recommendation(
                    priority="high",
                    category="network",
                    title="无法访问TikTok",
                    description="当前网络无法访问TikTok主域名",
                    solution="检查VPN连接，尝试更换VPN节点或协议"
                ))
            elif network_result.tiktok_connectivity.avg_latency_ms and \
                 network_result.tiktok_connectivity.avg_latency_ms > 500:
                recommendations.append(Recommendation(
                    priority="low",
                    category="network",
                    title="网络延迟过高",
                    description=f"访问TikTok的平均延迟为{network_result.tiktok_connectivity.avg_latency_ms:.0f}ms",
                    solution="选择地理位置更近的VPN节点以降低延迟"
                ))
        
        # 如果没有严重问题，添加一般性建议
        if not recommendations:
            recommendations.append(Recommendation(
                priority="low",
                category="general",
                title="继续保持",
                description="当前配置良好，风险较低",
                solution="定期检测以确保配置持续有效，避免频繁更换设备指纹"
            ))
        
        # 按优先级排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 4))
        
        return recommendations
    
    def get_risk_summary(self, report: DetectionReport) -> Dict[str, Any]:
        """生成风险摘要"""
        return {
            "overall_score": report.overall_score,
            "risk_level": report.overall_risk_level.value,
            "critical_issues": len([r for r in report.recommendations if r.priority == "critical"]),
            "high_issues": len([r for r in report.recommendations if r.priority == "high"]),
            "total_issues": len(report.all_issues),
            "top_recommendation": report.recommendations[0] if report.recommendations else None
        }


# 全局服务实例
risk_scoring_service = RiskScoringService()
