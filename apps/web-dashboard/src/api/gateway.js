import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

// HTTP 层错误（网络不通、后端 4xx/5xx）也归一化成 {code, message, traceId}
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const body = error.response && error.response.data
    const err = new Error((body && body.message) || error.message || '网络错误')
    err.code = (body && body.code) || error.code || 'NETWORK_ERROR'
    err.traceId = body && body.traceId
    return Promise.reject(err)
  },
)

// 后端统一响应 {code, message, data, traceId}：code !== 0 时按错误抛出
function unwrap(response) {
  const body = response.data
  if (body && body.code === 0) {
    return body
  }
  const err = new Error((body && body.message) || '请求失败')
  err.code = body && body.code
  err.traceId = body && body.traceId
  throw err
}

export async function runDemo(payload, idempotencyKey) {
  const response = await api.post('/v1/demo/run', payload, {
    headers: {
      'Idempotency-Key': idempotencyKey,
    },
  })
  return unwrap(response)
}

export async function getDemoStatus(businessId) {
  const response = await api.get(`/v1/demo/status/${businessId}`)
  return unwrap(response)
}
