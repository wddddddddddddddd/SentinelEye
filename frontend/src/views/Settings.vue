<template>
  <div>
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <i class="fas fa-cog text-4xl text-blue-500 mb-4"></i>
      <h2 class="text-2xl font-bold text-gray-800 mb-2">系统设置</h2>
      <p class="text-gray-600 mb-6">配置监控系统参数和通知偏好</p>
      <button class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg flex items-center mx-auto transition-colors">
        <i class="fas fa-save mr-2"></i> 保存设置
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings'
}
</script>