import client from './client'

export async function login({ email, password }) {
  const { data } = await client.post('/auth/login', { email, password })
  if (data?.access_token) {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('token_type', data.token_type)
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token)
    }
  }
  return data
}

export async function signup({ email, username, password, isPrivate = false }) {
  const { data } = await client.post('/users/', {
    email,
    username,
    password,
    is_private: isPrivate,
  })
  return data
}

export async function verifyEmail(token) {
  const { data } = await client.get('/auth/verify-email', { params: { token } })
  return data
}

export async function requestPasswordReset({ email }) {
  const { data } = await client.post('/auth/forgot-password', { email })
  return data
}

export async function resetPassword({ token, password, passwordConfirmation }) {
  const { data } = await client.post('/auth/reset-password', {
    token,
    password,
    password_confirmation: passwordConfirmation,
  })
  return data
}

export async function getCurrentUser() {
  const { data } = await client.get('/users/me')
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('token_type')
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem('access_token'))
}

export function extractApiError(err, fallback = 'Something went wrong') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  if (err?.message) return err.message
  return fallback
}
