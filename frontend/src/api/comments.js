import client from './client'

export async function fetchComments(postId, { limit = 20, skip = 0 } = {}) {
  const { data } = await client.get(`/comments/post/${postId}`, {
    params: { limit, skip },
  })
  return data
}

export async function createComment(postId, content) {
  const { data } = await client.post(`/comments/post/${postId}`, { content })
  return data
}

export async function updateComment(commentId, content) {
  const { data } = await client.put(`/comments/${commentId}`, { content })
  return data
}

export async function deleteComment(commentId) {
  const { data } = await client.delete(`/comments/${commentId}`)
  return data
}
