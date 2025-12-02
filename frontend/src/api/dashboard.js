// src/api/feedback.js
import axios from 'axios'

const apiClient = axios.create({
    baseURL: 'http://localhost:8888', // 你的 FastAPI 地址
    timeout: 5000
})

export const getRecentFeedbacks = (limit = 5) => {
    return apiClient.get('/feedback/recent', {
        params: { limit }
    })
}
