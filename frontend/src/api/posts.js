import client from './client'

export async function fetchPosts({ limit = 10, skip = 0, search } = {}) {
  const params = { limit, skip }
  if (search) params.search = search
  const { data } = await client.get('/posts/', { params })
  return data
}
