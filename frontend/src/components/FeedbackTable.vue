<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
    <div class="p-5 border-b border-gray-200 flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-800">实时用户反馈</h3>
      <button class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
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
          <tr v-for="(feedback, index) in feedbacks" :key="index" class="hover:bg-gray-50">
            <td class="py-4 px-6">
              <span :class="`tag tag-${feedback.type}`">{{ getTypeLabel(feedback.type) }}</span>
            </td>
            <td class="py-4 px-6" v-html="feedback.title">
            </td>
            <td class="py-4 px-6">{{ feedback.time }}</td>
            <td class="py-4 px-6">{{ feedback.user }}</td>
            <td class="py-4 px-6">
              <span :class="`status-${feedback.status} status-indicator`"></span>
              <span :class="`text-${feedback.status === 'replied' ? 'green' : 'red'}-600`">
                {{ feedback.status === 'replied' ? '已答复' : '待处理' }}
              </span>
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
  methods: {
    getTypeLabel(type) {
      const labels = {
        feedback: '问题反馈',
        service: '人工服务',
        solution: '解决方案',
        win10: 'win10专区'
      }
      return labels[type] || '其他'
    }
  }
}
</script>