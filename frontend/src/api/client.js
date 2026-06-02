import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) throw new Error('No refresh token')
  // Use raw axios so we don't recurse through this interceptor.
  const { data } = await axios.post(
    '/api/auth/refresh',
    { refresh_token: refreshToken },
    { headers: { 'Content-Type': 'application/json' } },
  )
  localStorage.setItem('access_token', data.access_token)
  return data.access_token
}

function clearSessionAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('token_type')
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error
    if (!response || response.status !== 401 || !config || config._retry) {
      return Promise.reject(error)
    }
    // Don't try to refresh for the auth endpoints themselves.
    const url = config.url || ''
    if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
      return Promise.reject(error)
    }

    config._retry = true
    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const newToken = await refreshPromise
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${newToken}`
      return client(config)
    } catch (refreshErr) {
      clearSessionAndRedirect()
      return Promise.reject(refreshErr)
    }
  },
)

export default client
