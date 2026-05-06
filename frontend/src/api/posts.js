import client from './client'

export async function fetchPosts({ limit = 10, skip = 0, search } = {}) {
  const params = { limit, skip }
  if (search) params.search = search
  const { data } = await client.get('/posts/', { params })
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
