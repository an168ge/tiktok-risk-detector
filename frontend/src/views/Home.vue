<template>
  <div class="min-h-screen py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <!-- 标题 -->
      <div class="text-center mb-12 fade-in">
        <h1 class="text-4xl md:text-5xl font-bold text-white mb-4">
          TikTok风险检测工具
        </h1>
        <p class="text-xl text-white/80">
          专业的TikTok访问环境检测 · 一键检测IP、DNS、指纹、设备等风险
        </p>
      </div>

      <!-- 检测按钮 -->
      <div class="text-center mb-8 fade-in" v-if="!detecting && !report">
        <button 
          @click="startDetection" 
          class="btn btn-primary text-lg px-12 py-4 shadow-xl hover:shadow-2xl transform hover:scale-105"
          :disabled="detecting"
        >
          <span v-if="!detecting">🔍 开始检测</span>
          <span v-else class="flex items-center">
            <svg class="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            检测中...
          </span>
        </button>
      </div>

      <!-- 检测进度 -->
      <div v-if="detecting" class="card mb-8 fade-in">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-16 h-16 mb-4">
            <svg class="animate-spin h-16 w-16 text-primary" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h3 class="text-xl font-semibold mb-2">正在检测中...</h3>
          <p class="text-gray-600">正在分析您的访问环境，请稍候</p>
          <div class="mt-4">
            <div class="text-sm text-gray-500">{{ detectionStatus }}</div>
          </div>
        </div>
      </div>

      <!-- 检测报告 -->
      <div v-if="report && !detecting" class="space-y-6 fade-in">
        <!-- 总体评分 -->
        <div class="card text-center">
          <div class="mb-4">
            <div class="inline-flex items-center justify-center w-32 h-32 rounded-full mb-4"
                 :class="getRiskClass(report.overall_risk_level) + ' border-4'">
              <div class="text-center">
                <div class="text-4xl font-bold">{{ report.overall_score.toFixed(0) }}</div>
                <div class="text-sm">分</div>
              </div>
            </div>
          </div>
          <h2 class="text-2xl font-bold mb-2">
            风险等级: {{ getRiskText(report.overall_risk_level) }}
          </h2>
          <p class="text-gray-600">{{ getRiskDescription(report.overall_risk_level) }}</p>
        </div>

        <!-- 各模块评分 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-600">IP质量</span>
              <span class="font-semibold">{{ report.score_breakdown.ip_score.toFixed(0) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full transition-all" 
                   :class="getScoreColor(report.score_breakdown.ip_score)"
                   :style="{ width: report.score_breakdown.ip_score + '%' }"></div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-600">隐私保护</span>
              <span class="font-semibold">{{ report.score_breakdown.privacy_score.toFixed(0) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full transition-all" 
                   :class="getScoreColor(report.score_breakdown.privacy_score)"
                   :style="{ width: report.score_breakdown.privacy_score + '%' }"></div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-600">指纹一致性</span>
              <span class="font-semibold">{{ report.score_breakdown.fingerprint_score.toFixed(0) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full transition-all" 
                   :class="getScoreColor(report.score_breakdown.fingerprint_score)"
                   :style="{ width: report.score_breakdown.fingerprint_score + '%' }"></div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-600">设备质量</span>
              <span class="font-semibold">{{ report.score_breakdown.device_score.toFixed(0) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full transition-all" 
                   :class="getScoreColor(report.score_breakdown.device_score)"
                   :style="{ width: report.score_breakdown.device_score + '%' }"></div>
            </div>
          </div>

          <div class="card">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-600">网络质量</span>
              <span class="font-semibold">{{ report.score_breakdown.network_score.toFixed(0) }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="h-2 rounded-full transition-all" 
                   :class="getScoreColor(report.score_breakdown.network_score)"
                   :style="{ width: report.score_breakdown.network_score + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- IP信息 -->
        <div class="card" v-if="report.ip_result">
          <h3 class="text-xl font-semibold mb-4">📍 IP信息</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-sm text-gray-600">IP地址</div>
              <div class="font-semibold">{{ report.ip_result.info.ip }}</div>
            </div>
            <div>
              <div class="text-sm text-gray-600">位置</div>
              <div class="font-semibold">
                {{ report.ip_result.info.country || '未知' }}, 
                {{ report.ip_result.info.city || '未知' }}
              </div>
            </div>
            <div>
              <div class="text-sm text-gray-600">ISP</div>
              <div class="font-semibold">{{ report.ip_result.info.isp || '未知' }}</div>
            </div>
            <div>
              <div class="text-sm text-gray-600">IP类型</div>
              <div class="font-semibold">
                <span :class="getIPTypeClass(report.ip_result.quality.ip_type)">
                  {{ getIPTypeText(report.ip_result.quality.ip_type) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 问题列表 -->
        <div class="card" v-if="report.all_issues && report.all_issues.length > 0">
          <h3 class="text-xl font-semibold mb-4">⚠️ 检测到的问题</h3>
          <div class="space-y-2">
            <div v-for="(issue, index) in report.all_issues" :key="index" 
                 class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-800">
              {{ issue }}
            </div>
          </div>
        </div>

        <!-- 修复建议 -->
        <div class="card" v-if="report.recommendations && report.recommendations.length > 0">
          <h3 class="text-xl font-semibold mb-4">💡 修复建议</h3>
          <div class="space-y-4">
            <div v-for="(rec, index) in report.recommendations" :key="index" 
                 class="border-l-4 pl-4 py-2"
                 :class="getPriorityClass(rec.priority)">
              <div class="flex items-center mb-2">
                <span class="px-2 py-1 text-xs font-semibold rounded mr-2"
                      :class="getPriorityBadgeClass(rec.priority)">
                  {{ getPriorityText(rec.priority) }}
                </span>
                <span class="font-semibold">{{ rec.title }}</span>
              </div>
              <p class="text-sm text-gray-600 mb-2">{{ rec.description }}</p>
              <p class="text-sm text-gray-800">
                <strong>解决方案:</strong> {{ rec.solution }}
              </p>
            </div>
          </div>
        </div>

        <!-- 重新检测按钮 -->
        <div class="text-center">
          <button @click="resetDetection" class="btn btn-primary">
            🔄 重新检测
          </button>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="card bg-red-50 border-red-200 fade-in">
        <div class="text-center text-red-800">
          <h3 class="text-xl font-semibold mb-2">❌ 检测失败</h3>
          <p>{{ error }}</p>
          <button @click="resetDetection" class="mt-4 btn btn-secondary">
            重试
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { startDetection as startDetectionAPI } from '@/api/detection'
import FingerprintCollector from '@/utils/fingerprint'

const detecting = ref(false)
const detectionStatus = ref('')
const report = ref(null)
const error = ref(null)

// 开始检测
const startDetection = async () => {
  detecting.value = true
  error.value = null
  report.value = null

  try {
    // 1. 收集指纹信息
    detectionStatus.value = '正在收集浏览器指纹...'
    const fingerprint = await FingerprintCollector.collect()

    // 2. 发送到后端检测
    detectionStatus.value = '正在分析环境风险...'
    const response = await startDetectionAPI(fingerprint)

    if (response.success) {
      report.value = response.data
    } else {
      error.value = response.message || '检测失败'
    }
  } catch (err) {
    console.error('Detection error:', err)
    error.value = err.message || '检测过程中发生错误，请重试'
  } finally {
    detecting.value = false
    detectionStatus.value = ''
  }
}

// 重置检测
const resetDetection = () => {
  detecting.value = false
  report.value = null
  error.value = null
  detectionStatus.value = ''
}

// 获取风险等级样式
const getRiskClass = (level) => {
  const classes = {
    low: 'risk-low',
    medium: 'risk-medium',
    high: 'risk-high',
    critical: 'risk-critical'
  }
  return classes[level] || 'risk-medium'
}

// 获取风险等级文本
const getRiskText = (level) => {
  const texts = {
    low: '低风险 ✓',
    medium: '中等风险 ⚠️',
    high: '高风险 ⚠️',
    critical: '严重风险 ❌'
  }
  return texts[level] || '未知'
}

// 获取风险描述
const getRiskDescription = (level) => {
  const descriptions = {
    low: '您的访问环境配置良好，可以安全使用TikTok',
    medium: '存在一些风险因素，建议优化后使用',
    high: '存在较多风险，可能影响TikTok正常使用',
    critical: '环境风险严重，请立即修复后再使用'
  }
  return descriptions[level] || ''
}

// 获取分数颜色
const getScoreColor = (score) => {
  if (score >= 80) return 'bg-success'
  if (score >= 60) return 'bg-warning'
  if (score >= 40) return 'bg-orange-500'
  return 'bg-danger'
}

// 获取IP类型样式
const getIPTypeClass = (type) => {
  const classes = {
    residential: 'text-success',
    mobile: 'text-success',
    datacenter: 'text-warning',
    vpn: 'text-orange-500',
    proxy: 'text-danger',
    hosting: 'text-warning'
  }
  return classes[type] || 'text-gray-600'
}

// 获取IP类型文本
const getIPTypeText = (type) => {
  const texts = {
    residential: '住宅IP ✓',
    mobile: '移动IP ✓',
    datacenter: '数据中心IP',
    vpn: 'VPN IP',
    proxy: '代理IP',
    hosting: '托管IP',
    unknown: '未知'
  }
  return texts[type] || type
}

// 获取优先级样式
const getPriorityClass = (priority) => {
  const classes = {
    critical: 'border-danger',
    high: 'border-orange-500',
    medium: 'border-warning',
    low: 'border-blue-500'
  }
  return classes[priority] || 'border-gray-300'
}

// 获取优先级徽章样式
const getPriorityBadgeClass = (priority) => {
  const classes = {
    critical: 'bg-danger text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-warning text-white',
    low: 'bg-blue-500 text-white'
  }
  return classes[priority] || 'bg-gray-500 text-white'
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const texts = {
    critical: '紧急',
    high: '重要',
    medium: '中等',
    low: '一般'
  }
  return texts[priority] || priority
}
</script>

<style scoped>
/* 组件特定样式已在main.css中定义 */
</style>
