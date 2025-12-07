import axios from 'axios'

// 根据环境设置 baseURL
const baseURL = import.meta.env.DEV 
    ? 'http://localhost:8888' 
    : '/api'

const apiClient = axios.create({
    baseURL: baseURL,
    timeout: 10000
})

// 获取关键词列表
export const getKeywords = () => {
  return apiClient.get('/keywords')
}

// 添加关键词
export const addKeyword = (keyword) => {
  return apiClient.post('/keywords', { keyword })
}

// 删除关键词
export const deleteKeyword = (keyword) => {
  return apiClient.delete(`/keywords/${encodeURIComponent(keyword)}`)
}

// 更新关键词
export const updateKeyword = (oldKeyword, newKeyword) => {
  return apiClient.put('/keywords', null, {
    params: { 
      old: oldKeyword, 
      new: newKeyword 
    }
  })
}
