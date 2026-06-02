import { useEffect, useRef, useState } from 'react'
import { updateProfile } from '@/api/users'
import { extractApiError } from '@/api/auth'

export function EditProfileModal({ user, onClose, onSaved }) {
  const [bio, setBio] = useState(user.bio ?? '')
  const [isPrivate, setIsPrivate] = useState(Boolean(user.is_private))
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(user.profile_picture ?? null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' && !saving) onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose, saving])

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const handleFileChange = (e) => {
    const picked = e.target.files?.[0] ?? null
    setFile(picked)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (saving) return
    setSaving(true)
    setError('')

    const payload = {}
    if (bio !== (user.bio ?? '')) payload.bio = bio
    if (isPrivate !== Boolean(user.is_private)) payload.isPrivate = isPrivate
    if (file) payload.file = file

    if (Object.keys(payload).length === 0) {
      setSaving(false)
      onClose()
      return
    }

    try {
      const updated = await updateProfile(payload)
      onSaved(updated)
    } catch (err) {
      setError(extractApiError(err, 'Failed to update profile'))
    } finally {
      setSaving(false)
    }
  }

  const username = user.username ?? 'me'
  const avatarLetter = username.charAt(0).toUpperCase()

  return (
    <div
      className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center p-3"
      style={{ background: 'rgba(0,0,0,0.55)', zIndex: 1050 }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !saving) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Edit profile"
    >
      <div
        className="bg-white rounded-4 shadow-lg w-100"
        style={{ maxWidth: 480 }}
      >
        <div className="d-flex align-items-center px-4 py-3 border-bottom">
          <h2 className="h6 mb-0 fw-semibold">Edit profile</h2>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            aria-label="Close"
            className="btn btn-link p-1 text-dark ms-auto"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <div className="d-flex align-items-center gap-3 mb-4">
            <div className="avatar-ring" style={{ width: 72, height: 72, padding: 2 }}>
              {preview ? (
                <img
                  src={preview}
                  alt={username}
                  className="avatar-inner"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <div
                  className="avatar-inner"
                  style={{ width: '100%', height: '100%', fontSize: 28 }}
                >
                  {avatarLetter}
                </div>
              )}
            </div>
            <div className="flex-grow-1">
              <div className="fw-semibold">{username}</div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn btn-link p-0 small text-primary text-decoration-none"
              >
                Change profile photo
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="d-none"
              />
            </div>
          </div>

          <div className="mb-3">
            <label htmlFor="edit-bio" className="form-label small fw-semibold">
              Bio
            </label>
            <textarea
              id="edit-bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              rows={3}
              maxLength={150}
              placeholder="Tell people about yourself"
              className="form-control"
            />
            <div className="text-secondary small text-end mt-1">{bio.length}/150</div>
          </div>

          <div className="form-check mb-4">
            <input
              id="edit-private"
              type="checkbox"
              checked={isPrivate}
              onChange={(e) => setIsPrivate(e.target.checked)}
              className="form-check-input"
            />
            <label htmlFor="edit-private" className="form-check-label small">
              Private account
              <div className="text-secondary" style={{ fontSize: 12 }}>
                Only approved followers can see your posts.
              </div>
            </label>
          </div>

          <div className="d-flex justify-content-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="btn btn-light btn-pill"
            >
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn btn-primary btn-pill">
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
