<template>
  <div>
    <!-- 调试面板 -->
    <div v-if="debug" class="fixed top-4 left-4 bg-gray-900 text-white p-4 rounded-lg text-xs z-50 opacity-90">
      <div class="font-bold mb-2">调试信息</div>
      <div>keywords: {{ keywords }}</div>
      <div>length: {{ keywords.length }}</div>
      <div>loading: {{ loading }}</div>
      <div>error: {{ error }}</div>
      <button @click="debug = false" class="mt-2 text-red-400 hover:text-red-300 transition-colors">
        关闭调试
      </button>
    </div>

    <!-- 气泡通知 -->
    <div v-if="showNotification" class="fixed top-4 right-4 z-50 animate-fade-in-down">
      <div :class="[
        'px-4 py-3 rounded-lg shadow-lg border-l-4 flex items-center',
        notificationType === 'success'
          ? 'bg-green-50 border-green-500 text-green-700'
          : 'bg-red-50 border-red-500 text-red-700'
      ]">
        <i :class="[
          'mr-3 text-lg',
          notificationType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'
        ]"></i>
        <div class="flex-1">
          <p class="font-medium">{{ notificationMessage }}</p>
        </div>
        <button @click="showNotification = false" class="ml-4 text-gray-400 hover:text-gray-600">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- 编辑关键词模态框 -->
    <div v-if="showEditModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-md transform transition-all animate-scale-in">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl font-bold text-gray-800 flex items-center">
              <i class="fas fa-edit text-blue-500 mr-2"></i>
              编辑关键词
            </h3>
            <button @click="closeEditModal" class="text-gray-400 hover:text-gray-600 transition-colors">
              <i class="fas fa-times text-lg"></i>
            </button>
          </div>

          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              原关键词
            </label>
            <div class="bg-gray-50 px-4 py-3 rounded-lg border border-gray-200 text-gray-600">
              {{ editingKeyword.old }}
            </div>
          </div>

          <div class="mb-8">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              新关键词
            </label>
            <input v-model="editingKeyword.new" type="text" placeholder="请输入新的关键词..."
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              @keyup.enter="saveEditKeyword" />
            <p v-if="editError" class="mt-2 text-sm text-red-600 flex items-center">
              <i class="fas fa-exclamation-circle mr-1"></i> {{ editError }}
            </p>
          </div>

          <div class="flex justify-end space-x-3">
            <button @click="closeEditModal"
              class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
              取消
            </button>
            <button @click="saveEditKeyword" :disabled="savingEdit" :class="[
              'px-4 py-2 bg-blue-500 text-white rounded-lg transition-colors',
              savingEdit ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'
            ]">
              <i v-if="savingEdit" class="fas fa-spinner fa-spin mr-2"></i>
              <i v-else class="fas fa-save mr-2"></i>
              保存修改
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div v-if="showDeleteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-md transform transition-all animate-scale-in">
        <div class="p-6">
          <div class="flex items-center mb-6">
            <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mr-4">
              <i class="fas fa-exclamation-triangle text-red-500 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-bold text-gray-800">确认删除</h3>
              <p class="text-gray-600 mt-1">此操作不可恢复</p>
            </div>
          </div>

          <div class="mb-8">
            <p class="text-gray-700">
              确定要删除关键词
              <span class="font-bold text-red-600 mx-1">"{{ deletingKeyword }}"</span>
              吗？
            </p>
            <p class="text-sm text-gray-500 mt-2">
              删除后，系统将不再监控包含该关键词的反馈
            </p>
          </div>

          <div class="flex justify-end space-x-3">
            <button @click="closeDeleteModal"
              class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
              取消
            </button>
            <button @click="confirmDeleteKeyword" :disabled="deleting" :class="[
              'px-4 py-2 bg-red-500 text-white rounded-lg transition-colors',
              deleting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-red-600'
            ]">
              <i v-if="deleting" class="fas fa-spinner fa-spin mr-2"></i>
              <i v-else class="fas fa-trash mr-2"></i>
              确认删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-key text-blue-500 mr-3"></i>
        关键词管理
      </h2>
      <div class="flex space-x-2">
        <button @click="fetchKeywords" :disabled="loading" :class="[
          'bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors',
          loading ? 'opacity-50 cursor-not-allowed' : ''
        ]">
          <i :class="['mr-2', loading ? 'fas fa-spinner fa-spin' : 'fas fa-redo']"></i>
          {{ loading ? '加载中...' : '刷新列表' }}
        </button>
        <button @click="debug = !debug"
          class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
          <i class="fas fa-bug mr-2"></i>
          调试
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center mb-8 animate-pulse">
      <i class="fas fa-spinner fa-spin text-3xl text-blue-500 mb-4"></i>
      <p class="text-gray-600">正在加载关键词...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 animate-fade-in">
      <div class="flex items-center">
        <i class="fas fa-exclamation-circle text-red-500 mr-3"></i>
        <div>
          <h3 class="text-red-800 font-medium">加载失败</h3>
          <p class="text-red-600 text-sm">{{ error }}</p>
          <button @click="fetchKeywords" class="text-red-600 hover:text-red-800 text-sm mt-2 flex items-center">
            <i class="fas fa-redo mr-1"></i>重试
          </button>
        </div>
      </div>
    </div>

    <!-- 正常状态 -->
    <div v-else>
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8 animate-fade-in-up">
        <div class="p-5 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">当前监控关键词</h3>
          <div class="text-sm text-gray-500">
            <span v-if="keywords.length > 0" class="bg-blue-100 text-blue-800 px-3 py-1.5 rounded-full font-medium">
              共 {{ keywords.length }} 个关键词
            </span>
            <span v-else class="text-gray-400">暂无关键词</span>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="keywords.length === 0" class="p-8 text-center text-gray-500">
          <div class="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-search text-blue-400 text-2xl"></i>
          </div>
          <p class="text-lg font-medium text-gray-600 mb-2">暂无监控关键词</p>
          <p class="text-sm text-gray-500">点击下方添加按钮开始监控关键词</p>
        </div>

        <!-- 关键词列表 -->
        <div v-else class="p-5">
          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
            <div v-for="(keyword, index) in keywords" :key="index"
              class="keyword-item group bg-gradient-to-br from-gray-50 to-white hover:from-blue-50 hover:to-blue-100 rounded-xl p-4 flex justify-between items-center border border-gray-200 hover:border-blue-300 transition-all duration-300 hover:shadow-md hover:-translate-y-1">
              <div class="flex items-center">
                <div
                  class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3 group-hover:bg-blue-200 transition-colors">
                  <i class="fas fa-hashtag text-blue-500 text-sm"></i>
                </div>
                <span class="font-medium text-gray-800 group-hover:text-blue-700 transition-colors">
                  {{ keyword }}
                </span>
              </div>
              <div class="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 flex items-center justify-center transition-colors"
                  @click="openEditModal(index)" title="编辑关键词">
                  <i class="fas fa-edit text-sm"></i>
                </button>
                <button
                  class="w-8 h-8 rounded-full bg-red-100 text-red-600 hover:bg-red-200 flex items-center justify-center transition-colors"
                  @click="openDeleteModal(index)" title="删除关键词">
                  <i class="fas fa-trash text-sm"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="border-t pt-6">
            <!-- 添加关键词表单 -->
            <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <i class="fas fa-plus-circle text-blue-500 mr-2"></i>
              添加新关键词
            </h3>
            <div class="flex mb-3">
              <div class="relative flex-1">
                <input v-model="newKeyword" type="text" placeholder="例如：游戏、蓝屏、闪退..." :class="[
                  'w-full pl-10 pr-4 py-3 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                  newKeywordError ? 'border-red-300' : 'border-gray-300'
                ]" @keyup.enter="addKeyword" @input="newKeywordError = ''" />
                <i class="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              </div>
              <button :disabled="addingKeyword" @click="addKeyword" :class="[
                'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-6 rounded-r-lg flex items-center transition-all',
                addingKeyword ? 'opacity-50 cursor-not-allowed' : ''
              ]">
                <i :class="['mr-2', addingKeyword ? 'fas fa-spinner fa-spin' : 'fas fa-plus']"></i>
                {{ addingKeyword ? '添加中...' : '添加' }}
              </button>
            </div>
            <div v-if="newKeywordError" class="text-red-500 text-sm mb-2 flex items-center">
              <i class="fas fa-exclamation-circle mr-2"></i> {{ newKeywordError }}
            </div>
            <p class="text-sm text-gray-500">
              支持添加多个关键词，系统将实时监控包含这些关键词的反馈
            </p>
          </div>
        </div>
      </div>

      <!-- 图片关键词设置部分 -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 animate-fade-in-up">
        <div class="p-5">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <i class="fas fa-image text-purple-500 mr-2"></i>
            图片关键词设置
          </h3>
          <p class="text-gray-600 mb-4">
            系统支持通过图像识别技术检测截图中的问题。您可以设置需要监控的视觉关键词：
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="p-5 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all">
              <div class="flex items-center mb-4">
                <div
                  class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center mr-3">
                  <i class="fas fa-desktop text-blue-500 text-lg"></i>
                </div>
                <div>
                  <h4 class="font-medium text-gray-800">蓝屏检测</h4>
                  <p class="text-xs text-blue-600 mt-1">已启用</p>
                </div>
              </div>
              <p class="text-sm text-gray-600">检测用户截图中是否包含蓝屏错误画面</p>
            </div>

            <div class="p-5 border border-gray-200 rounded-xl hover:border-red-300 hover:shadow-sm transition-all">
              <div class="flex items-center mb-4">
                <div
                  class="w-12 h-12 rounded-full bg-gradient-to-br from-red-100 to-red-200 flex items-center justify-center mr-3">
                  <i class="fas fa-bug text-red-500 text-lg"></i>
                </div>
                <div>
                  <h4 class="font-medium text-gray-800">错误弹窗</h4>
                  <p class="text-xs text-red-600 mt-1">已启用</p>
                </div>
              </div>
              <p class="text-sm text-gray-600">检测用户截图中是否包含系统错误弹窗</p>
            </div>
          </div>

          <div class="mt-6">
            <button @click="configureImageRecognition"
              class="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white px-4 py-2 rounded-lg flex items-center transition-all">
              <i class="fas fa-cog mr-2"></i> 配置图片识别设置
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
//import { getKeywords, addKeyword, updateKeyword, deleteKeyword } from '../api/keywords.js'
//const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'
const API_BASE = '/api'  // 直接使用 /api，由Nginx代理
export default {
  name: 'Keywords',
  setup() {
    const keywords = ref([])
    const newKeyword = ref('')
    const newKeywordError = ref('')
    const loading = ref(false)
    const addingKeyword = ref(false)
    const error = ref(null)
    const debug = ref(false)

    // 模态框状态
    const showEditModal = ref(false)
    const showDeleteModal = ref(false)
    const editingKeyword = ref({ old: '', new: '' })
    const editError = ref('')
    const savingEdit = ref(false)
    const deletingKeyword = ref('')
    const deleting = ref(false)

    // 气泡通知状态
    const showNotification = ref(false)
    const notificationType = ref('success') // 'success' 或 'error'
    const notificationMessage = ref('')

    // 显示气泡通知
    const showToast = (type, message, duration = 3000) => {
      notificationType.value = type
      notificationMessage.value = message
      showNotification.value = true

      setTimeout(() => {
        showNotification.value = false
      }, duration)
    }

    // 获取关键词列表
    const fetchKeywords = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await axios.get(`${API_BASE}/keywords`)
        keywords.value = response.data || []
      } catch (err) {
        console.error('获取关键词失败:', err)
        error.value = err.response?.data?.detail || err.message || '获取关键词失败'
        keywords.value = []
      } finally {
        loading.value = false
      }
    }

    // 添加关键词
    const addKeyword = async () => {
      const keyword = newKeyword.value.trim()

      if (!keyword) {
        newKeywordError.value = '请输入关键词'
        return
      }

      if (keywords.value.includes(keyword)) {
        newKeywordError.value = '该关键词已存在'
        return
      }

      addingKeyword.value = true
      newKeywordError.value = ''

      try {
        const response = await axios.post(`${API_BASE}/keywords`, { keyword })
        keywords.value = response.data.keywords || []
        newKeyword.value = ''

        // 显示成功气泡
        showToast('success', `关键词"${keyword}"添加成功`)
      } catch (err) {
        console.error('添加关键词失败:', err)
        newKeywordError.value = err.response?.data?.detail || '添加失败，请重试'
        showToast('error', '添加失败')
      } finally {
        addingKeyword.value = false
      }
    }

    // 打开编辑模态框
    const openEditModal = (index) => {
      editingKeyword.value = {
        old: keywords.value[index],
        new: keywords.value[index]
      }
      editError.value = ''
      showEditModal.value = true
    }

    // 关闭编辑模态框
    const closeEditModal = () => {
      showEditModal.value = false
      editingKeyword.value = { old: '', new: '' }
      editError.value = ''
    }

    // 保存编辑的关键词
    const saveEditKeyword = async () => {
      const oldKeyword = editingKeyword.value.old
      const newKeywordValue = editingKeyword.value.new.trim()

      if (!newKeywordValue) {
        editError.value = '请输入新的关键词'
        return
      }

      if (newKeywordValue === oldKeyword) {
        closeEditModal()
        return
      }

      if (keywords.value.includes(newKeywordValue)) {
        editError.value = '该关键词已存在'
        return
      }

      savingEdit.value = true

      try {
        const response = await axios.put(`${API_BASE}/keywords`, null, {
          params: {
            old: oldKeyword,
            new: newKeywordValue
          }
        })

        keywords.value = response.data.keywords || []
        closeEditModal()

        // 显示成功气泡
        showToast('success', `关键词已从"${oldKeyword}"修改为"${newKeywordValue}"`)
      } catch (err) {
        console.error('更新关键词失败:', err)
        editError.value = err.response?.data?.detail || '更新失败，请重试'
        showToast('error', '更新失败')
      } finally {
        savingEdit.value = false
      }
    }

    // 打开删除确认模态框
    const openDeleteModal = (index) => {
      deletingKeyword.value = keywords.value[index]
      showDeleteModal.value = true
    }

    // 关闭删除确认模态框
    const closeDeleteModal = () => {
      showDeleteModal.value = false
      deletingKeyword.value = ''
    }

    // 确认删除关键词
    const confirmDeleteKeyword = async () => {
      deleting.value = true

      try {
        const response = await axios.delete(`${API_BASE}/keywords/${encodeURIComponent(deletingKeyword.value)}`)
        keywords.value = response.data.keywords || []
        closeDeleteModal()

        // 显示成功气泡
        showToast('success', `关键词"${deletingKeyword.value}"删除成功`)
      } catch (err) {
        console.error('删除关键词失败:', err)
        showToast('error', err.response?.data?.detail || '删除失败，请重试')
      } finally {
        deleting.value = false
      }
    }

    // 配置图片识别设置
    const configureImageRecognition = () => {
      showToast('info', '图片识别设置功能开发中...', 2000)
    }

    // 初始化时加载关键词
    onMounted(() => {
      fetchKeywords()
    })

    return {
      keywords,
      newKeyword,
      newKeywordError,
      loading,
      addingKeyword,
      error,
      debug,

      // 模态框相关
      showEditModal,
      showDeleteModal,
      editingKeyword,
      editError,
      savingEdit,
      deletingKeyword,
      deleting,

      // 气泡通知相关
      showNotification,
      notificationType,
      notificationMessage,

      // 方法
      fetchKeywords,
      addKeyword,
      openEditModal,
      closeEditModal,
      saveEditKeyword,
      openDeleteModal,
      closeDeleteModal,
      confirmDeleteKeyword,
      configureImageRecognition
    }
  }
}
</script>

<style scoped>
/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

.animate-fade-in-down {
  animation: fadeInDown 0.3s ease-out;
}

.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}

.animate-scale-in {
  animation: scaleIn 0.3s ease-out;
}
</style>
