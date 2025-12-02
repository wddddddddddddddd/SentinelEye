<template>
  <div>
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <i class="fas fa-file-pdf text-4xl text-blue-500 mb-4"></i>
      <h2 class="text-2xl font-bold text-gray-800 mb-2">报告生成</h2>
      <p class="text-gray-600 mb-6">创建和下载用户反馈的周报和月报分析</p>
      <button class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg flex items-center mx-auto transition-colors">
        <i class="fas fa-download mr-2"></i> 生成PDF报告
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Reports'
}
</script>