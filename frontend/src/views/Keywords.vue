<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-key text-blue-500 mr-3"></i>
        关键词管理
      </h2>
      <div>
        <button class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
          <i class="fas fa-history mr-2"></i> 查看触发记录
        </button>
      </div>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="p-5 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-800">当前监控关键词</h3>
      </div>
      <div class="p-5">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div 
            v-for="(keyword, index) in keywords" 
            :key="index"
            class="keyword-item bg-gray-50 rounded-lg p-4 flex justify-between items-center border border-gray-200"
          >
            <span class="font-medium">{{ keyword }}</span>
            <div class="flex space-x-2">
              <button class="text-blue-500 hover:text-blue-700" @click="editKeyword(index)">
                <i class="fas fa-edit"></i>
              </button>
              <button class="text-red-500 hover:text-red-700" @click="deleteKeyword(index)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
        
        <div class="border-t pt-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">添加新关键词</h3>
          <div class="flex">
            <input 
              v-model="newKeyword"
              type="text" 
              placeholder="输入要监控的关键词..." 
              class="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              @keyup.enter="addKeyword"
            >
            <button 
              class="bg-blue-500 hover:bg-blue-600 text-white px-6 rounded-r-lg flex items-center transition-colors"
              @click="addKeyword"
            >
              <i class="fas fa-plus mr-2"></i> 添加
            </button>
          </div>
          <p class="mt-2 text-sm text-gray-500">支持添加多个关键词，系统将实时监控包含这些关键词的反馈</p>
        </div>
      </div>
    </div>
    
    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="p-5">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">图片关键词设置</h3>
        <p class="text-gray-600 mb-4">系统支持通过图像识别技术检测截图中的问题。您可以设置需要监控的视觉关键词：</p>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center mb-3">
              <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                <i class="fas fa-desktop text-blue-500"></i>
              </div>
              <h4 class="font-medium">蓝屏检测</h4>
            </div>
            <p class="text-sm text-gray-600">检测用户截图中是否包含蓝屏错误画面</p>
          </div>
          
          <div class="p-4 border border-gray-200 rounded-lg">
            <div class="flex items-center mb-3">
              <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center mr-3">
                <i class="fas fa-bug text-red-500"></i>
              </div>
              <h4 class="font-medium">错误弹窗</h4>
            </div>
            <p class="text-sm text-gray-600">检测用户截图中是否包含系统错误弹窗</p>
          </div>
        </div>
        
        <div class="mt-6">
          <button class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
            <i class="fas fa-cog mr-2"></i> 配置图片识别设置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Keywords',
  setup() {
    const keywords = ref(['游戏', '蓝屏', '闪退', '病毒', '勒索', '崩溃'])
    const newKeyword = ref('')

    const addKeyword = () => {
      if (newKeyword.value.trim()) {
        keywords.value.push(newKeyword.value.trim())
        newKeyword.value = ''
      }
    }

    const deleteKeyword = (index) => {
      keywords.value.splice(index, 1)
    }

    const editKeyword = (index) => {
      const newKeyword = prompt('编辑关键词:', keywords.value[index])
      if (newKeyword !== null && newKeyword.trim()) {
        keywords.value[index] = newKeyword.trim()
      }
    }

    return {
      keywords,
      newKeyword,
      addKeyword,
      deleteKeyword,
      editKeyword
    }
  }
}
</script>