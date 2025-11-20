"""
检测API端点
"""
from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging

from app.schemas import (
    DetectionRequest, DetectionReport, APIResponse, RiskLevel
)
from app.services.ip_service import ip_detection_service
from app.services.fingerprint_service import fingerprint_service
from app.services.dns_service import dns_detection_service
from app.services.webrtc_service import webrtc_detection_service
from app.services.device_service import device_detection_service
from app.services.network_service import network_detection_service
from app.services.risk_scoring_service import risk_scoring_service
from app.core.rate_limit import check_rate_limit
from app.core.cache import redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start", response_model=APIResponse, dependencies=[Depends(check_rate_limit)])
async def start_detection(
    request: Request,
    detection_req: DetectionRequest,
    background_tasks: BackgroundTasks
) -> APIResponse:
    """
    开始完整检测
    
    这是主要的检测端点，会执行所有检测项并返回完整报告
    """
    try:
        # 获取客户端IP
        client_ip = request.client.host
        
        # 如果有X-Forwarded-For头（反向代理），使用其中的IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        logger.info(f"Starting detection for IP: {client_ip}")
        
        # 准备检测数据
        detection_data = detection_req.model_dump()
        detection_data["client_ip"] = client_ip
        
        # 1. IP检测
        ip_result = await ip_detection_service.detect_full(client_ip)
        logger.info(f"IP detection completed: {ip_result.risk_level}")
        
        # 将IP国家信息添加到检测数据中，用于后续一致性分析
        if ip_result.info.country_code:
            detection_data["ip_country_code"] = ip_result.info.country_code
        
        # 2. 指纹检测
        fingerprint_result = await fingerprint_service.analyze_fingerprint(detection_data)
        logger.info(f"Fingerprint detection completed: {fingerprint_result.risk_level}")
        
        # 3. DNS检测
        dns_result = None
        if detection_req.dns_servers:
            dns_result = await dns_detection_service.detect_full(
                dns_servers=detection_req.dns_servers,
                expected_country=ip_result.info.country_code,
                vpn_ip=client_ip
            )
            logger.info(f"DNS detection completed: {dns_result.risk_level}")
        
        # 4. WebRTC检测
        webrtc_result = None
        if detection_req.webrtc_ips:
            webrtc_result = await webrtc_detection_service.detect_full(
                webrtc_ips=detection_req.webrtc_ips,
                vpn_ip=client_ip,
                real_ip=None  # 可以从其他来源获取真实IP
            )
            logger.info(f"WebRTC detection completed: {webrtc_result.risk_level}")
        
        # 5. 设备检测
        device_result = await device_detection_service.detect_full(
            user_agent=detection_data["user_agent"],
            platform=detection_data["platform"],
            data=detection_data
        )
        logger.info(f"Device detection completed: {device_result.risk_level}")
        
        # 6. 网络质量检测
        network_result = await network_detection_service.detect_full()
        logger.info(f"Network detection completed: {network_result.risk_level}")
        
        # 生成综合报告
        report = await risk_scoring_service.generate_report(
            ip_result=ip_result,
            dns_result=dns_result,
            webrtc_result=webrtc_result,
            fingerprint_result=fingerprint_result,
            device_result=device_result,
            network_result=network_result
        )
        
        # 异步保存到数据库（可选）
        # background_tasks.add_task(save_detection_record, report)
        
        # 缓存报告（1小时）
        cache_key = redis_client.make_key("detection_report", report.detection_id)
        await redis_client.set(cache_key, report.model_dump(), ttl=3600)
        
        logger.info(
            f"Detection completed: ID={report.detection_id}, "
            f"Score={report.overall_score}, Level={report.overall_risk_level}"
        )
        
        return APIResponse(
            success=True,
            message="Detection completed successfully",
            data=report.model_dump()
        )
    
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/{detection_id}", response_model=APIResponse)
async def get_detection_result(detection_id: str) -> APIResponse:
    """
    获取检测结果
    
    根据检测ID获取之前的检测报告
    """
    try:
        # 从缓存获取
        cache_key = redis_client.make_key("detection_report", detection_id)
        cached_report = await redis_client.get(cache_key)
        
        if cached_report:
            return APIResponse(
                success=True,
                data=cached_report
            )
        
        # 从数据库获取（如果有）
        # report = await get_report_from_db(detection_id)
        # if report:
        #     return APIResponse(success=True, data=report)
        
        raise HTTPException(status_code=404, detail="Detection result not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get detection result error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ip", response_model=APIResponse, dependencies=[Depends(check_rate_limit)])
async def detect_ip(request: Request) -> APIResponse:
    """
    单独IP检测
    
    只执行IP检测，返回IP相关信息和风险评估
    """
    try:
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        result = await ip_detection_service.detect_full(client_ip)
        
        return APIResponse(
            success=True,
            message="IP detection completed",
            data=result.model_dump()
        )
    
    except Exception as e:
        logger.error(f"IP detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fingerprint", response_model=APIResponse, dependencies=[Depends(check_rate_limit)])
async def detect_fingerprint(
    request: Request,
    detection_req: DetectionRequest
) -> APIResponse:
    """
    单独指纹检测
    
    只执行浏览器指纹检测和一致性分析
    """
    try:
        detection_data = detection_req.model_dump()
        result = await fingerprint_service.analyze_fingerprint(detection_data)
        
        return APIResponse(
            success=True,
            message="Fingerprint detection completed",
            data=result.model_dump()
        )
    
    except Exception as e:
        logger.error(f"Fingerprint detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-check", response_model=APIResponse)
async def quick_check(request: Request) -> APIResponse:
    """
    快速检查
    
    返回基本的IP信息和风险等级，用于首页快速展示
    """
    try:
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # 只获取IP基础信息和质量评估
        info = await ip_detection_service.get_ip_info(client_ip)
        quality = await ip_detection_service.check_ip_quality(client_ip)
        
        # 简单的风险评估
        risk_score = ip_detection_service._calculate_risk_score(quality)
        
        if risk_score >= 80:
            risk_level = "low"
            message = "环境良好"
        elif risk_score >= 60:
            risk_level = "medium"
            message = "存在中等风险"
        elif risk_score >= 40:
            risk_level = "high"
            message = "存在较高风险"
        else:
            risk_level = "critical"
            message = "存在严重风险"
        
        return APIResponse(
            success=True,
            message=message,
            data={
                "ip": info.ip,
                "location": f"{info.country or 'Unknown'}, {info.city or 'Unknown'}",
                "isp": info.isp,
                "ip_type": quality.ip_type.value,
                "is_vpn": quality.is_vpn,
                "is_proxy": quality.is_proxy,
                "risk_score": round(risk_score, 1),
                "risk_level": risk_level
            }
        )
    
    except Exception as e:
        logger.error(f"Quick check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
