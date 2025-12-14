// api/keywords.js
import axios from 'axios'

// 根据环境变量动态设置 baseURL
const getBaseURL = () => {
  // 开发环境使用本地服务器
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888'
  }
  // 生产环境使用 /api 前缀（由 Nginx 代理）
  return '/api'
}

const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000
})

// 添加请求拦截器，方便调试
apiClient.interceptors.request.use(
  config => {
    if (import.meta.env.DEV) {
      console.log(`请求: ${config.method.toUpperCase()} ${config.baseURL}${config.url}`)
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

export const getKeywords = () => {
  return apiClient.get('/api/keywords')
}

export const addKeyword = (keyword) => {
  return apiClient.post('/api/keywords', { keyword })
}

export const deleteKeyword = (keyword) => {
  return apiClient.delete(`/api/keywords/${encodeURIComponent(keyword)}`)
}

export const updateKeyword = (oldKeyword, newKeyword) => {
  return apiClient.put('/api/keywords', null, {
    params: {
      old: oldKeyword,
      new: newKeyword
    }
  })
}