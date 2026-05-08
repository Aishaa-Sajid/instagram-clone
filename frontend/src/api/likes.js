import client from './client'

export async function toggleLike(postId) {
  const { data } = await client.post(`/likes/${postId}`)
  return data
}
