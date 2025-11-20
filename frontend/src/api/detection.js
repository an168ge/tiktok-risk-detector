/**
 * 检测相关API
 */
import request from './request';

/**
 * 快速检查
 */
export function quickCheck() {
  return request({
    url: '/detection/quick-check',
    method: 'get'
  });
}

/**
 * 开始完整检测
 */
export function startDetection(data) {
  return request({
    url: '/detection/start',
    method: 'post',
    data
  });
}

/**
 * 获取检测结果
 */
export function getDetectionResult(detectionId) {
  return request({
    url: `/detection/${detectionId}`,
    method: 'get'
  });
}

/**
 * 单独IP检测
 */
export function detectIP() {
  return request({
    url: '/detection/ip',
    method: 'post'
  });
}

/**
 * 单独指纹检测
 */
export function detectFingerprint(data) {
  return request({
    url: '/detection/fingerprint',
    method: 'post',
    data
  });
}

export default {
  quickCheck,
  startDetection,
  getDetectionResult,
  detectIP,
  detectFingerprint
};
