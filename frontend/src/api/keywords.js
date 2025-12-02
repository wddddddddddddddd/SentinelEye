// src/api/keywords.js - 方案2：直接使用axios
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8888'

// 获取关键词列表
export const getKeywords = () => {
  return axios.get(`${BASE_URL}/keywords`)
}

// 添加关键词
export const addKeyword = (keyword) => {
  return axios.post(`${BASE_URL}/keywords`, { keyword })
}

// 删除关键词
export const deleteKeyword = (keyword) => {
  return axios.delete(`${BASE_URL}/keywords/${encodeURIComponent(keyword)}`)
}

// 更新关键词
export const updateKeyword = (oldKeyword, newKeyword) => {
  return axios.put(`${BASE_URL}/keywords`, null, {
    params: { 
      old: oldKeyword, 
      new: newKeyword 
    }
  })
}