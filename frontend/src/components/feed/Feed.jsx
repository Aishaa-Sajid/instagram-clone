import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchPosts } from '@/api/posts'
import { extractApiError, logout } from '@/api/auth'
import { useNavigate } from 'react-router-dom'
import logoSvg from '@/assets/logo.svg'
import { PostCard } from './PostCard'
import { CreatePostForm } from './CreatePostForm'

const PAGE_SIZE = 10

export function Feed() {
  const [posts, setPosts] = useState([])
  const [skip, setSkip] = useState(0)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [error, setError] = useState('')
  const sentinelRef = useRef(null)
  const loadingRef = useRef(false)
  const navigate = useNavigate()

  const loadMore = useCallback(async () => {
    if (loadingRef.current || !hasMore) return
    loadingRef.current = true
    setLoading(true)
    setError('')
    try {
      const data = await fetchPosts({ limit: PAGE_SIZE, skip })
      const batch = Array.isArray(data) ? data : []
      setPosts((prev) => [...prev, ...batch])
      setSkip((prev) => prev + batch.length)
      if (batch.length < PAGE_SIZE) setHasMore(false)
    } catch (err) {
      setError(extractApiError(err, 'Failed to load posts'))
    } finally {
      loadingRef.current = false
      setLoading(false)
    }
  }, [hasMore, skip])

  useEffect(() => {
    loadMore()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const node = sentinelRef.current
    if (!node || !hasMore) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore()
      },
      { rootMargin: '400px 0px' }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [loadMore, hasMore])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="d-flex flex-column min-vh-100">
      <header className="feed-header">
        <div className="feed-header-inner container-md d-flex align-items-center px-3 px-md-4">
          <div className="d-flex align-items-center gap-2">
            <img src={logoSvg} alt="Instagram" width="26" height="26" />
            <span className="font-display gradient-text">Instagram</span>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="btn btn-sm btn-light btn-pill ms-auto"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="flex-grow-1 py-3 py-md-4">
        <div className="feed-container mx-auto px-0 px-sm-3">
          <CreatePostForm onCreated={(post) => setPosts((prev) => [post, ...prev])} />

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}

          {loading && (
            <div className="d-flex justify-content-center py-4">
              <div className="spinner-border text-secondary" role="status" aria-label="Loading">
                <span className="visually-hidden">Loading…</span>
              </div>
            </div>
          )}

          {!loading && !hasMore && posts.length > 0 && (
            <p className="text-center text-secondary small py-3 mb-0">You're all caught up.</p>
          )}

          {!loading && posts.length === 0 && !error && (
            <p className="text-center text-secondary py-5 mb-0">No posts yet.</p>
          )}

          <div ref={sentinelRef} style={{ height: 1 }} />
        </div>
      </main>
    </div>
  )
}
