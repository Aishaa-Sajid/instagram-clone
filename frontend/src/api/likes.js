import client from './client'

export async function toggleLike(postId) {
  const { data } = await client.post(`/likes/${postId}`)
  return data
}

export async function fetchPostLikes(postId, { limit = 20, skip = 0 } = {}) {
  const { data } = await client.get(`/likes/${postId}/likes`, {
    params: { limit, skip },
  })
  return Array.isArray(data) ? data : []
}
