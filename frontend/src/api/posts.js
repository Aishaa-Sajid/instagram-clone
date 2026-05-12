import client from './client'

export async function fetchPosts({ limit = 10, skip = 0, search } = {}) {
  const params = { limit, skip }
  if (search) params.search = search
  const { data } = await client.get('/posts/', { params })
  return data
}

export async function fetchPost(id) {
  const { data } = await client.get(`/posts/${id}`)
  return data
}

export async function createPost({ caption, files }) {
  const form = new FormData()
  form.append('caption', caption ?? '')
  for (const file of files) form.append('files', file)
  const { data } = await client.post('/posts/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function updatePost(id, { caption, files = [], imagesToDelete = [] } = {}) {
  const form = new FormData()
  if (caption !== undefined && caption !== null) form.append('caption', caption)
  for (const imageId of imagesToDelete) form.append('images_to_delete', String(imageId))
  for (const file of files) form.append('new_images', file)
  const { data } = await client.put(`/posts/${id}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
