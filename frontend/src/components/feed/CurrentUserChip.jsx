import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { logout } from '@/api/auth'
import { clearCurrentUserCache, useCurrentUser } from '@/hooks/useCurrentUser'

export function CurrentUserChip() {
  const { user, loading } = useCurrentUser()
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return
    const onDocClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (loading && !user) {
    return (
      <div className="d-flex align-items-center gap-2" aria-busy="true">
        <div className="avatar-ring" style={{ width: 28, height: 28 }}>
          <div className="avatar-inner" style={{ width: 24, height: 24 }} />
        </div>
      </div>
    )
  }

  if (!user) return null

  const username = user.username ?? 'me'
  const avatarLetter = username.charAt(0).toUpperCase()

  const goToProfile = () => {
    setOpen(false)
    navigate(`/users/${user.id}`)
  }

  const handleLogout = () => {
    logout()
    clearCurrentUserCache()
    setOpen(false)
    navigate('/login', { replace: true })
  }

  return (
    <div className="position-relative d-flex align-items-center" ref={wrapperRef}>
      <button
        type="button"
        onClick={goToProfile}
        title={`View ${username}'s profile`}
        className="btn btn-link p-1 text-decoration-none text-dark d-flex align-items-center gap-2"
      >
        <div className="avatar-ring" style={{ width: 28, height: 28 }}>
          {user.profile_picture ? (
            <img
              src={user.profile_picture}
              alt={username}
              className="avatar-inner"
              style={{ width: 24, height: 24, objectFit: 'cover' }}
            />
          ) : (
            <div className="avatar-inner" style={{ width: 24, height: 24, fontSize: 12 }}>
              {avatarLetter}
            </div>
          )}
        </div>
        <span className="fw-semibold small d-none d-sm-inline">{username}</span>
      </button>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className="btn btn-link p-1 text-dark"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}
        >
          <path d="M7 10l5 5 5-5z" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="position-absolute end-0 mt-1 bg-white border rounded-3 shadow-sm"
          style={{ top: '100%', minWidth: 160, zIndex: 1000 }}
        >
          <button
            type="button"
            role="menuitem"
            onClick={goToProfile}
            className="btn btn-link w-100 text-start text-decoration-none text-dark small px-3 py-2"
          >
            View profile
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={handleLogout}
            className="btn btn-link w-100 text-start text-decoration-none text-dark small px-3 py-2"
          >
            Log out
          </button>
        </div>
      )}
    </div>
  )
}
