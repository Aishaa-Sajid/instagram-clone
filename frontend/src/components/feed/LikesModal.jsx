import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchPostLikes } from '@/api/likes'
import { extractApiError } from '@/api/auth'

const PAGE_SIZE = 20

export function LikesModal({ postId, onClose }) {
  const [likes, setLikes] = useState([])
  const [skip, setSkip] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const loadMore = useCallback(
    async (reset = false) => {
      if (loading) return
      const nextSkip = reset ? 0 : skip
      setLoading(true)
      setError('')
      try {
        const batch = await fetchPostLikes(postId, { limit: PAGE_SIZE, skip: nextSkip })
        setLikes((prev) => (reset ? batch : [...prev, ...batch]))
        setSkip(nextSkip + batch.length)
        setHasMore(batch.length === PAGE_SIZE)
      } catch (err) {
        setError(extractApiError(err, 'Failed to load likes'))
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [postId, skip, loading]
  )

  useEffect(() => {
    loadMore(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const goToProfile = (userId) => {
    if (userId == null) return
    onClose()
    navigate(`/users/${userId}`)
  }

  return (
    <div
      className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center p-3"
      style={{ background: 'rgba(0,0,0,0.55)', zIndex: 1050 }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Likes"
    >
      <div
        className="bg-white rounded-4 shadow-lg w-100 d-flex flex-column"
        style={{ maxWidth: 400, maxHeight: '80vh' }}
      >
        <div className="d-flex align-items-center justify-content-center position-relative px-4 py-3 border-bottom">
          <h2 className="h6 mb-0 fw-semibold">Likes</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="btn btn-link p-1 text-dark position-absolute end-0 me-2"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>

        <div className="overflow-auto px-2 py-2" style={{ flex: 1 }}>
          {error && (
            <div className="alert alert-danger py-2 small mx-2" role="alert">
              {error}
            </div>
          )}

          {likes.length === 0 && !loading && !error && (
            <p className="text-secondary small text-center my-4 mb-0">No likes yet.</p>
          )}

          <ul className="list-unstyled mb-0">
            {likes.map((like) => {
              const user = like.user ?? {}
              const username = user.username ?? 'unknown'
              const avatarLetter = username.charAt(0).toUpperCase()
              return (
                <li key={like.id}>
                  <button
                    type="button"
                    onClick={() => goToProfile(user.id)}
                    className="btn btn-link text-decoration-none text-dark w-100 text-start d-flex align-items-center gap-3 px-3 py-2"
                  >
                    <div className="avatar-ring" style={{ width: 44, height: 44 }}>
                      {user.profile_picture ? (
                        <img
                          src={user.profile_picture}
                          alt={username}
                          className="avatar-inner"
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      ) : (
                        <div
                          className="avatar-inner"
                          style={{ width: '100%', height: '100%', fontSize: 16 }}
                        >
                          {avatarLetter}
                        </div>
                      )}
                    </div>
                    <span className="fw-semibold small">{username}</span>
                  </button>
                </li>
              )
            })}
          </ul>

          {hasMore && (
            <div className="text-center py-2">
              <button
                type="button"
                className="btn btn-sm btn-light btn-pill"
                onClick={() => loadMore(false)}
                disabled={loading}
              >
                {loading ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}

          {loading && likes.length === 0 && (
            <div className="d-flex justify-content-center py-4">
              <div className="spinner-border spinner-border-sm text-secondary" role="status" aria-label="Loading">
                <span className="visually-hidden">Loading…</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
