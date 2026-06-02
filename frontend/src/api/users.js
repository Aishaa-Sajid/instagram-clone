import client from './client'

export async function fetchUser(id) {
  const { data } = await client.get(`/users/${id}`)
  return data
}

export async function updateProfile({ bio, isPrivate, file } = {}) {
  const params = {}
  if (bio !== undefined && bio !== null) params.bio = bio
  if (isPrivate !== undefined && isPrivate !== null) params.is_private = isPrivate

  const form = new FormData()
  if (file) form.append('file', file)

  const { data } = await client.put('/users/update-profile', form, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
