import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken')

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,

  (error) => {
    const status = error.response?.status
    const requestUrl = error.config?.url ?? ''

    const isLoginRequest =
      requestUrl.includes('/auth/login')

    if (status === 401 && !isLoginRequest) {
      localStorage.removeItem('accessToken')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

export default apiClient