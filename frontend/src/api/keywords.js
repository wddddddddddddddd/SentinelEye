import axios from 'axios'

// 生产环境统一使用 /api 前缀
const apiClient = axios.create({
    baseURL: '/api',
    timeout: 10000
})

export const getKeywords = () => {
  return apiClient.get('/keywords')
}

export const addKeyword = (keyword) => {
  return apiClient.post('/keywords', { keyword })
}

export const deleteKeyword = (keyword) => {
  return apiClient.delete(`/keywords/${encodeURIComponent(keyword)}`)
}

export const updateKeyword = (oldKeyword, newKeyword) => {
  return apiClient.put('/keywords', null, {
    params: {
      old: oldKeyword,
      new: newKeyword
    }
  })
}
