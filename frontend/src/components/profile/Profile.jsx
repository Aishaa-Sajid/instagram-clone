import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchUser } from '@/api/users'
import { extractApiError } from '@/api/auth'
import { setCurrentUserCache, useCurrentUser } from '@/hooks/useCurrentUser'
import { Navbar } from '@/components/layout/Navbar'
import { EditProfileModal } from './EditProfileModal'

export function Profile() {
  const { id } = useParams()
  const { user: currentUser } = useCurrentUser()

  const isOwn = currentUser && String(currentUser.id) === String(id)
  const seeded = isOwn ? currentUser : null

  const [user, setUser] = useState(seeded)
  const [loading, setLoading] = useState(!seeded)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setError('')
      if (!seeded) setLoading(true)
      try {
        const data = await fetchUser(id)
        if (!cancelled) setUser(data)
      } catch (err) {
        if (!cancelled) setError(extractApiError(err, 'Failed to load profile'))
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

  const username = user?.username ?? ''
  const avatarLetter = username.charAt(0).toUpperCase()

  return (
    <div className="d-flex flex-column min-vh-100">
      <Navbar />

      <main className="flex-grow-1 py-3 py-md-4">
        <div className="feed-container mx-auto px-3">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {loading && !user && (
            <div className="d-flex justify-content-center py-5">
              <div className="spinner-border text-secondary" role="status" aria-label="Loading">
                <span className="visually-hidden">Loading…</span>
              </div>
            </div>
          )}

          {user && (
            <section className="profile-card">
              <div className="profile-cover" />
              <div className="profile-body">
                <div className="profile-avatar-wrap">
                  <div className="avatar-ring profile-avatar">
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
                        style={{ width: '100%', height: '100%', fontSize: 44 }}
                      >
                        {avatarLetter}
                      </div>
                    )}
                  </div>
                </div>

                <div className="profile-info">
                  <div className="profile-name-row">
                    <div className="d-flex align-items-center gap-2 flex-wrap">
                      <h1 className="h4 mb-0 fw-semibold">{username}</h1>
                      {user.is_private && (
                        <span className="profile-tag" title="Private account">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M12 1a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V11a2 2 0 0 0-2-2h-2V6a5 5 0 0 0-5-5zm-3 8V6a3 3 0 1 1 6 0v3H9z" />
                          </svg>
                          Private
                        </span>
                      )}
                    </div>
                    {isOwn && (
                      <button
                        type="button"
                        onClick={() => setEditing(true)}
                        className="edit-profile-btn"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                        </svg>
                        Edit profile
                      </button>
                    )}
                  </div>
                  {user.email && <div className="profile-email">{user.email}</div>}
                  {user.bio ? (
                    <p className="profile-bio mb-0">{user.bio}</p>
                  ) : (
                    <p className="profile-bio-empty mb-0">
                      {isOwn ? 'Add a bio to tell people about yourself.' : 'No bio yet.'}
                    </p>
                  )}
                </div>
              </div>
            </section>
          )}

          {!loading && !user && !error && (
            <p className="text-center text-secondary py-5 mb-0">User not found.</p>
          )}
        </div>
      </main>

      {editing && user && isOwn && (
        <EditProfileModal
          user={user}
          onClose={() => setEditing(false)}
          onSaved={(updated) => {
            setUser(updated)
            setCurrentUserCache(updated)
            setEditing(false)
          }}
        />
      )}
    </div>
  )
}
