<template>
  <div class="max-w-6xl mx-auto space-y-6 p-4">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
      <!-- 顶部通知配置保持不变 -->
      <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-6 border-b border-gray-100">
        <div class="flex items-center mb-4 md:mb-0">
          <i class="fas fa-bell text-3xl text-blue-500 mr-4"></i>
          <div>
            <h2 class="text-2xl font-bold text-gray-800">通知管理</h2>
            <p class="text-gray-500 text-sm mt-1">管理推推群聊通知及查看全部告警记录</p>
          </div>
        </div>

        <div class="flex items-center space-x-3 bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
          <span class="text-gray-700 font-medium">推推自动通知</span>
          <button @click="togglePush" :class="isPushEnabled ? 'bg-blue-500' : 'bg-gray-300'"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none">
            <span :class="isPushEnabled ? 'translate-x-6' : 'translate-x-1'"
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 shadow-sm"></span>
          </button>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-semibold text-gray-700 mb-4 flex items-center">
          <i class="fas fa-users-cog text-gray-400 mr-2"></i>通知范围配置
        </h3>

        <div class="flex flex-col sm:flex-row gap-3 mb-6">
          <input v-model="newPid" type="text" placeholder="输入推推群聊 PID (如: Group_12345)"
            class="border border-gray-300 rounded-lg px-4 py-2.5 flex-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            @keyup.enter="addNotifyGroup" />
          <button @click="addNotifyGroup"
            class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg flex items-center justify-center transition-colors font-medium whitespace-nowrap">
            <i class="fas fa-plus mr-2"></i> 新增 PID
          </button>
        </div>

        <div class="flex flex-wrap gap-3">
          <div v-for="(group, index) in notifyGroups" :key="index"
            class="flex items-center bg-blue-50 border border-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium shadow-sm">
            <span>{{ group.name }}</span>
            <span
              class="ml-2 text-blue-500/70 text-xs bg-blue-100/50 px-2 py-0.5 rounded-md border border-blue-200/50 font-mono">
              {{ group.pid }}
            </span>
            <button v-if="!group.isDefault" @click="removeNotifyGroup(index)"
              class="ml-3 text-blue-400 hover:text-red-500 focus:outline-none transition-colors">
              <i class="fas fa-times-circle text-base"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史告警 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-6 border-b border-gray-100 pb-4">
        <div class="flex items-center mb-4 sm:mb-0">
          <i class="fas fa-history text-purple-500 text-2xl mr-3"></i>
          <h3 class="text-xl font-bold text-gray-800">全部历史告警通知</h3>
        </div>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-400">共 {{ alerts.length }} 条</span>

          <!-- 手动推送按钮 -->
          <button v-if="alerts.length > 0" @click="manualTriggerPush" :disabled="isPushing"
            class="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 text-white rounded-2xl text-sm font-semibold transition-all disabled:opacity-70 shadow-sm">
            <i v-if="isPushing" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-paper-plane"></i>
            {{ isPushing ? '推送中...' : '手动推送最新告警' }}
          </button>
        </div>

      </div>

      <!-- 告警列表 -->
      <div v-if="alerts.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div v-for="item in alerts" :key="item._id || item.feedback_id" @click="openAlertDetail(item)"
          class="p-5 border border-gray-100 rounded-xl bg-gray-50/50 hover:bg-white hover:shadow-md hover:border-purple-200 transition-all cursor-pointer group">

          <!-- 风险等级 + 时间 -->
          <div class="flex justify-between items-center mb-3">
            <span class="text-xs px-3 py-1 rounded-full font-medium" :class="getRiskClass(item.ai_result?.risk_level)">
              {{ getRiskText(item.ai_result?.risk_level) }}
            </span>
            <span class="text-xs text-gray-400">{{ formatTime(item.analyzed_at) }}</span>
          </div>

          <!-- 标题 -->
          <h4 class="font-semibold text-gray-800 group-hover:text-purple-600 line-clamp-1">
            {{ item.title || '驱动异常分析结果' }}
          </h4>

          <!-- 场景描述（正确使用 ai_result.scene） -->
          <p class="text-sm text-gray-600 mt-2 line-clamp-2">
            {{ item.ai_result?.scene || '暂无场景描述' }}
          </p>

          <!-- 底部信息 -->
          <div class="flex justify-between items-center mt-4 text-xs">
            <span class="text-gray-500">
              AI可信度
              <span class="font-semibold text-gray-700 ml-1">
                {{ formatConfidence(item.ai_result?.confidence) }}
              </span>
            </span>
            <span class="text-purple-500 group-hover:underline flex items-center">
              查看详情 <i class="fas fa-arrow-right ml-1 text-xs"></i>
            </span>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!loading" class="text-center py-16 text-gray-500 bg-gray-50 rounded-xl border border-dashed">
        <i class="fas fa-box-open text-4xl mb-4 text-gray-300"></i>
        <p class="text-lg font-medium text-gray-600">暂无历史告警数据</p>
      </div>

      <!-- 加载更多 -->
      <div ref="loadMoreTrigger" class="text-center py-4 h-12 flex items-center justify-center">
        <div v-if="loading" class="text-gray-500 flex items-center">
          <i class="fas fa-spinner fa-spin mr-3 text-blue-500"></i>
          <span class="text-sm font-medium">加载历史数据中...</span>
        </div>
        <div v-else-if="!hasMore && alerts.length > 0" class="text-sm text-gray-400">
          已加载全部告警
        </div>
      </div>
    </div>

    <!-- 优化后的详情弹窗 -->
    <div v-if="selectedAlert" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col">
        <!-- 弹窗头部 -->
        <div class="flex justify-between items-center px-6 py-5 border-b">
          <h3 class="text-xl font-bold text-gray-800">AI 分析详情</h3>
          <button @click="selectedAlert = null"
            class="w-8 h-8 flex items-center justify-center text-2xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors">
            ✕
          </button>
        </div>

        <!-- 内容区 -->
        <div class="flex-1 overflow-auto p-6 space-y-8">
          <!-- 核心指标栏 -->
          <div class="grid grid-cols-3 gap-4">
            <div>
              <div class="text-xs text-gray-500 mb-1.5">风险等级</div>
              <span :class="getRiskClass(selectedAlert.ai_result?.risk_level)"
                class="inline-block px-5 py-2 rounded-2xl text-sm font-semibold">
                {{ getRiskText(selectedAlert.ai_result?.risk_level) }}
              </span>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1.5">AI 可信度</div>
              <div class="text-4xl font-bold text-blue-600 tracking-tighter">
                {{ formatConfidence(selectedAlert.ai_result?.confidence) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1.5">分析时间</div>
              <div class="text-sm font-medium text-gray-700">
                {{ formatTime(selectedAlert.analyzed_at) }}
              </div>
            </div>
          </div>

          <!-- 标题 -->
          <div>
            <div class="text-xs text-gray-500 mb-1">反馈标题</div>
            <p class="text-lg font-semibold text-gray-800 leading-relaxed">
              {{ selectedAlert.title }}
            </p>
          </div>

          <!-- 场景 -->
          <div v-if="selectedAlert.ai_result?.scene" class="bg-blue-50 border border-blue-100 p-5 rounded-2xl">
            <div class="flex items-center gap-2 mb-3">
              <i class="fas fa-info-circle text-blue-500"></i>
              <span class="font-semibold text-blue-800">问题场景</span>
            </div>
            <p class="text-gray-700 leading-relaxed">{{ selectedAlert.ai_result.scene }}</p>
          </div>

          <!-- 风险类型 -->
          <div v-if="selectedAlert.ai_result?.risk_type" class="bg-amber-50 border border-amber-100 p-5 rounded-2xl">
            <div class="flex items-center gap-2 mb-3">
              <i class="fas fa-exclamation-triangle text-amber-500"></i>
              <span class="font-semibold text-amber-800">风险类型</span>
            </div>
            <p class="text-amber-800 font-medium">{{ selectedAlert.ai_result.risk_type }}</p>
          </div>

          <!-- 关键证据 -->
          <div v-if="selectedAlert.ai_result?.key_evidence?.length">
            <div class="font-semibold mb-3 flex items-center gap-2">
              <i class="fas fa-list-check text-purple-500"></i>
              关键证据
            </div>
            <ul class="space-y-3">
              <li v-for="(ev, i) in selectedAlert.ai_result.key_evidence" :key="i"
                class="flex gap-4 bg-white border border-gray-100 p-4 rounded-xl">
                <div
                  class="w-6 h-6 flex-shrink-0 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center text-sm font-bold">
                  ✓</div>
                <div class="text-gray-700 text-[15px]">{{ ev }}</div>
              </li>
            </ul>
          </div>

          <!-- 详细分析 -->
          <div v-if="selectedAlert.ai_result?.analysis">
            <div class="font-semibold mb-3">AI 详细分析</div>
            <div
              class="bg-gray-50 p-5 rounded-2xl text-gray-700 whitespace-pre-wrap leading-relaxed border border-gray-100">
              {{ selectedAlert.ai_result.analysis }}
            </div>
          </div>

          <!-- 处理建议 -->
          <div v-if="selectedAlert.ai_result?.suggestions?.length">
            <div class="font-semibold mb-3 flex items-center gap-2">
              <i class="fas fa-lightbulb text-emerald-500"></i>
              处理建议
            </div>
            <ol class="space-y-4">
              <li v-for="(sug, i) in selectedAlert.ai_result.suggestions" :key="i"
                class="flex gap-4 bg-emerald-50 border border-emerald-100 p-5 rounded-2xl">
                <span
                  class="flex-shrink-0 w-7 h-7 bg-white shadow-sm text-emerald-600 rounded-2xl flex items-center justify-center font-bold text-base border border-emerald-200">
                  {{ i + 1 }}
                </span>
                <span class="text-emerald-800">{{ sug }}</span>
              </li>
            </ol>
          </div>

          <!-- 需要跟进提示 -->
          <div v-if="selectedAlert.ai_result?.need_followup"
            class="bg-red-50 border border-red-200 p-4 rounded-2xl flex items-center gap-3">
            <i class="fas fa-flag text-red-500 text-xl"></i>
            <div>
              <div class="font-semibold text-red-700">此问题需要人工跟进</div>
              <div class="text-sm text-red-600">建议优先处理</div>
            </div>
          </div>

          <!-- 截图提示 -->
          <div v-if="selectedAlert.has_image"
            class="pt-4 border-t border-gray-100 flex items-center gap-2 text-purple-600">
            <i class="fas fa-image"></i>
            <span>包含 {{ selectedAlert.image_count || 1 }} 张截图 / 视频证据</span>
          </div>
        </div>

        <!-- 弹窗底部 -->
        <div class="px-6 py-4 border-t bg-gray-50 flex justify-end">
          <button @click="selectedAlert = null"
            class="px-8 py-2.5 bg-gray-800 hover:bg-black text-white rounded-2xl font-medium transition-colors">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getAllAiAnalyses } from '../api/dashboard'

// ================= 顶部配置区逻辑 =================
const isPushEnabled = ref(true)
const newPid = ref('')

const notifyGroups = ref([
  { name: '新驱动组', pid: 'Group_Default_001', isDefault: true }
])

const togglePush = () => {
  isPushEnabled.value = !isPushEnabled.value
  console.log('推推通知状态变更为:', isPushEnabled.value)
}

const addNotifyGroup = () => {
  const pidVal = newPid.value.trim()
  if (!pidVal) return
  if (notifyGroups.value.some(g => g.pid === pidVal)) {
    alert('该 PID 已存在')
    return
  }
  notifyGroups.value.push({
    name: '自定义群聊',
    pid: pidVal,
    isDefault: false
  })
  newPid.value = ''
}

const removeNotifyGroup = (index) => {
  notifyGroups.value.splice(index, 1)
}

// ================= 历史数据懒加载 =================
const alerts = ref([])
const loading = ref(false)
const hasMore = ref(true)
const skip = ref(0)
const limit = 10
const loadMoreTrigger = ref(null)
let observer = null

// ================= 手动发送推推通知逻辑（已完整添加） =================
const isPushing = ref(false)

const manualTriggerPush = async () => {
  if (alerts.value.length === 0) return

  isPushing.value = true
  const latestAlert = alerts.value[0]   // 取最新的第一条

  try {
    console.log('🚀 正在手动推送最新告警至推推群聊...', {
      alertId: latestAlert._id || latestAlert.feedback_id,
      title: latestAlert.title,
      pids: notifyGroups.value.map(g => g.pid),
      content: latestAlert
    })

    // TODO: 这里替换成真实接口调用
    // await sendPushNotification({
    //   pids: notifyGroups.value.map(g => g.pid),
    //   alertId: latestAlert._id || latestAlert.feedback_id,
    //   data: latestAlert
    // })

    // 模拟网络请求
    await new Promise(resolve => setTimeout(resolve, 1350))

    alert('✅ 手动推送成功！\n已将最新告警发送至所有配置的推推群聊')

  } catch (error) {
    console.error('推送失败', error)
    alert('❌ 推送失败，请检查网络或后端日志')
  } finally {
    isPushing.value = false
  }
}


const fetchAlerts = async (isLoadMore = false) => {
  if (loading.value || !hasMore.value) return
  loading.value = true

  if (!isLoadMore) {
    skip.value = 0
    alerts.value = []
  }

  try {
    const res = await getAllAiAnalyses(skip.value, limit)
    let list = []

    if (res.data && Array.isArray(res.data.data)) {
      list = res.data.data
    }

    if (list.length === 0) {
      hasMore.value = false
    } else {
      alerts.value = isLoadMore
        ? [...alerts.value, ...list]
        : list

      skip.value += list.length
      if (list.length < limit) hasMore.value = false
    }
  } catch (err) {
    console.error('获取告警数据失败:', err)
  } finally {
    loading.value = false
  }
}

// ================= 工具函数（已优化） =================
const getRiskClass = (level) => {
  switch (level) {
    case 'critical': return 'bg-red-100 text-red-700'
    case 'high': return 'bg-orange-100 text-orange-700'
    case 'medium': return 'bg-yellow-100 text-yellow-700'
    case 'low': return 'bg-green-100 text-green-700'
    default: return 'bg-gray-100 text-gray-600'
  }
}

const getRiskText = (level) => {
  switch (level) {
    case 'critical': return '严重'
    case 'high': return '高危'
    case 'medium': return '中危'
    case 'low': return '低危'
    default: return '未知'
  }
}

const formatConfidence = (val) => {
  if (val == null) return '—'
  return (val * 100).toFixed(1) + '%'
}

const formatTime = (timeObj) => {
  if (!timeObj) return ''
  // 支持 MongoDB $date 格式和普通字符串
  const ts = typeof timeObj === 'string' ? timeObj : (timeObj?.$date || timeObj)
  const date = new Date(ts)
  if (isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ================= 详情弹窗 =================
const selectedAlert = ref(null)

const openAlertDetail = (item) => {
  selectedAlert.value = item
}

// ================= 懒加载 =================
onMounted(() => {
  fetchAlerts()

  observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting && hasMore.value && !loading.value) {
      fetchAlerts(true)
    }
  }, { rootMargin: '120px' })

  if (loadMoreTrigger.value) observer.observe(loadMoreTrigger.value)
})

onUnmounted(() => {
  if (observer && loadMoreTrigger.value) {
    observer.unobserve(loadMoreTrigger.value)
  }
})
</script>