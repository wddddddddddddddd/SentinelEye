<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
    <div class="p-5 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-800">实时用户反馈</h3>
      <button @click="$emit('export')"
        class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
        <i class="fas fa-download mr-2"></i> 导出数据
      </button>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="py-3 px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">问题类型</th>
            <th class="py-3 px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">标题</th>
            <th class="py-3 px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">发布时间</th>
            <th class="py-3 px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户</th>
            <th class="py-3 px-6 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="(feedback, index) in processedFeedbacks" :key="feedback.post_id || index" class="hover:bg-gray-50">
            <td class="py-4 px-6">
              <span :class="`tag tag-${getCategoryClass(feedback.category)}`">{{ feedback.category }}</span>
            </td>
            <td class="py-4 px-6">
              <div class="flex items-center">
                <a :href="feedback.url" target="_blank"
                  class="text-blue-600 hover:text-blue-800 hover:underline truncate max-w-md" :title="feedback.title">
                  {{ feedback.title }}
                  <span v-if="feedback.has_attachment" class="ml-2 text-blue-500">
                    <i class="fas fa-image"></i>
                  </span>
                </a>
                <button v-if="!feedback.is_notified" @click="$emit('notify', feedback)"
                  class="ml-2 text-xs bg-red-100 text-red-600 hover:bg-red-200 px-2 py-1 rounded" title="标记为已通知">
                  需通知
                </button>
              </div>
            </td>
            <td class="py-4 px-6 whitespace-nowrap">{{ formatTime(feedback.created_at) }}</td>
            <td class="py-4 px-6">{{ feedback.username }}</td>
            <td class="py-4 px-6">
              <div class="flex items-center">
                <span :class="`status-${getStatusClass(feedback.status)} status-indicator`"></span>
                <span :class="`text-${getStatusColor(feedback.status)}-600 font-medium`">
                  {{ feedback.status || '待处理' }}
                </span>
                <span v-if="feedback.reply_count !== undefined" class="ml-2 text-xs text-gray-500">
                  <i class="fas fa-comment mr-0.5"></i>{{ feedback.reply_count }}
                </span>
                <span v-if="feedback.view_count !== undefined" class="ml-2 text-xs text-gray-500">
                  <i class="fas fa-eye mr-0.5"></i>{{ feedback.view_count }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FeedbackTable',
  props: {
    feedbacks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['export', 'notify', 'view-detail', 'mark-replied', 'delete'],
  computed: {
    processedFeedbacks() {
      // 对数据进行预处理，确保数据格式统一
      return this.feedbacks.map(feedback => ({
        post_id: feedback.post_id || `feedback_${Date.now()}_${Math.random()}`,
        title: feedback.title || '',
        username: feedback.username || feedback.user_id || '匿名用户',
        category: feedback.category || '其他',
        status: feedback.status || '待处理',
        has_attachment: feedback.has_attachment || (feedback.images && feedback.images.length > 0),
        created_at: feedback.created_at || new Date().toISOString(),
        view_count: feedback.view_count || 0,
        reply_count: feedback.reply_count || 0,
        url: feedback.url || '#',
        content: feedback.content || '',
        images: feedback.images || [],
        tags: feedback.tags || [],
        is_notified: feedback.is_notified || false
      }))
    }
  },
  methods: {
    // 将中文分类转换为样式类名
    getCategoryClass(category) {
      const categoryMap = {
        '问题反馈': 'feedback',
        '人工服务': 'service',
        '解决方案': 'solution',
        'win10专区': 'win10',
        '其他': 'other'
      }
      return categoryMap[category] || 'other'
    },

    // 将状态转换为样式类名
    getStatusClass(status) {
      // 已答复状态
      const repliedStatuses = ['已答复', '已处理', '已解决', 'replied', 'resolved']
      if (repliedStatuses.includes(status)) {
        return 'replied'
      }

      // 待处理状态
      const pendingStatuses = ['新人帖', '未处理', '待处理', 'pending', 'new']
      if (pendingStatuses.includes(status) || !status) {
        return 'pending'
      }

      return 'pending' // 默认视为待处理
    },

    // 获取状态颜色
    getStatusColor(status) {
      const repliedStatuses = ['已答复', '已处理', '已解决', 'replied', 'resolved']
      if (repliedStatuses.includes(status)) {
        return 'green'
      }
      return 'red'
    },

    // 格式化时间
    formatTime(timeString) {
      if (!timeString) return ''

      // 尝试解析时间字符串
      try {
        const date = new Date(timeString)
        if (isNaN(date.getTime())) {
          // 如果不是标准的Date字符串，直接返回原字符串
          return timeString
        }

        // 如果是今天，显示时间
        const today = new Date()
        if (date.toDateString() === today.toDateString()) {
          return date.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
          })
        }

        // 如果是今年，显示月-日 时:分
        if (date.getFullYear() === today.getFullYear()) {
          return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
        }

        // 其他情况显示完整日期
        return date.toLocaleDateString('zh-CN')
      } catch (error) {
        return timeString
      }
    }
  }
}
</script>

<style scoped>
/* 确保表格列宽合适 */
table {
  table-layout: auto;
}

/* 标题列自适应宽度 */
td:nth-child(2) {
  min-width: 300px;
  max-width: 500px;
}

/* 确保状态指示器有正确的颜色 */
.status-replied {
  background-color: #10b981;
}

.status-pending {
  background-color: #ef4444;
}
</style>