import { useEffect, useRef, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { fetchPost } from '@/api/posts'
import { extractApiError } from '@/api/auth'
import { Navbar } from '@/components/layout/Navbar'
import { PostCard } from './PostCard'
import { CommentsSection } from './CommentsSection'

export function PostDetail() {
  const { id } = useParams()
  const location = useLocation()
  const seeded = location.state?.post && String(location.state.post.id) === String(id)
    ? location.state.post
    : null

  const [post, setPost] = useState(seeded)
  const [loading, setLoading] = useState(!seeded)
  const [error, setError] = useState('')
  const commentsRef = useRef(null)
  const commentsScrolledRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setError('')
      if (!seeded) setLoading(true)
      try {
        const data = await fetchPost(id)
        if (!cancelled) setPost(data)
      } catch (err) {
        if (!cancelled) setError(extractApiError(err, 'Failed to load post'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    if (location.hash !== '#comments' || !post || commentsScrolledRef.current) return
    const node = document.getElementById('comments')
    if (!node) return
    node.scrollIntoView({ behavior: 'smooth', block: 'start' })
    commentsRef.current?.focusInput()
    commentsScrolledRef.current = true
  }, [post, location.hash])

  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />

      <main className="flex-grow-1 py-3 py-md-4">
        <div className="feed-container mx-auto px-0 px-sm-3">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {loading && !post && (
            <div className="d-flex justify-content-center py-5">
              <div className="spinner-border text-secondary" role="status" aria-label="Loading">
                <span className="visually-hidden">Loading…</span>
              </div>
            </div>
          )}

          {post && (
            <>
              <PostCard post={post} onUpdated={setPost} />
              <CommentsSection ref={commentsRef} post={post} />
            </>
          )}

          {!loading && !post && !error && (
            <p className="text-center text-secondary py-5 mb-0">Post not found.</p>
          )}
        </div>
      </main>
    </div>
  )
}
