<template>
  <div>
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <i class="fas fa-bell text-4xl text-blue-500 mb-4"></i>
      <h2 class="text-2xl font-bold text-gray-800 mb-2">通知记录</h2>
      <p class="text-gray-600 mb-6">查看所有关键词触发的通知记录和历史警报</p>
      <button class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg flex items-center mx-auto transition-colors">
        <i class="fas fa-history mr-2"></i> 加载通知记录
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Notifications'
}
</script>