import axios from 'axios'

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 15_000,
})

apiClient.interceptors.request.use((config) => {
  // 每个请求携带 X-Request-ID，与后端日志贯穿对齐
  config.headers['X-Request-ID'] = crypto.randomUUID()
  return config
})
