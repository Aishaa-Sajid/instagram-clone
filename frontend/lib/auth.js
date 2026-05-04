import client from './client'

export async function login({ email, password }) {
  const { data } = await client.post('/auth/login', { email, password })
  if (data?.access_token) {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('token_type', data.token_type)
  }
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem('access_token'))
}
