import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createComment,
  deleteComment,
  fetchComments,
  updateComment,
} from '@/api/comments'
import { extractApiError } from '@/api/auth'
import { useCurrentUser } from '@/hooks/useCurrentUser'

const PAGE_SIZE = 20

function formatRelative(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  const diff = (Date.now() - date.getTime()) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d`
  return date.toLocaleDateString()
}

function CommentRow({ comment, canEdit, canDelete, onEdit, onDelete, busy }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(comment.content)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const editRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!editing) return
    const node = editRef.current
    if (!node) return
    node.focus()
    const end = node.value.length
    node.setSelectionRange(end, end)
  }, [editing])

  const user = comment.user ?? {}
  const username = user.username ?? 'unknown'
  const avatarLetter = username.charAt(0).toUpperCase()

  const openProfile = () => {
    if (user?.id != null) navigate(`/users/${user.id}`)
  }

  const startEdit = () => {
    setDraft(comment.content)
    setEditing(true)
    setError('')
  }

  const cancelEdit = () => {
    setDraft(comment.content)
    setEditing(false)
    setError('')
  }

  const saveEdit = async () => {
    const next = draft.trim()
    if (!next) {
      setError('Comment cannot be empty')
      return
    }
    if (next === comment.content) {
      setEditing(false)
      return
    }
    setSaving(true)
    setError('')
    try {
      await onEdit(comment.id, next)
      setEditing(false)
    } catch (err) {
      setError(extractApiError(err, 'Failed to update comment'))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = () => {
    if (!window.confirm('Delete this comment?')) return
    onDelete(comment.id)
  }

  return (
    <li className="d-flex gap-2 py-2">
      <button
        type="button"
        onClick={openProfile}
        className="btn btn-link p-0 border-0 flex-shrink-0"
        aria-label={`View ${username}'s profile`}
      >
        <div className="avatar-ring" style={{ width: 32, height: 32 }}>
          {user.profile_picture ? (
            <img
              src={user.profile_picture}
              alt={username}
              className="avatar-inner"
              style={{ width: '100%', height: '100%', objectFit: 'cover', fontSize: 12 }}
            />
          ) : (
            <div className="avatar-inner" style={{ width: '100%', height: '100%', fontSize: 12 }}>
              {avatarLetter}
            </div>
          )}
        </div>
      </button>
      <div className="flex-grow-1 min-w-0">
        {editing ? (
          <div className="comment-edit-card">
            <div className="comment-edit-header">
              <span className="comment-edit-label">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                </svg>
                Editing comment
              </span>
              <span className={`comment-edit-counter ${draft.length > 480 ? 'is-warn' : ''}`}>
                {draft.length}/500
              </span>
            </div>
            <textarea
              ref={editRef}
              className="comment-edit-input"
              rows={2}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  e.preventDefault()
                  cancelEdit()
                } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                  e.preventDefault()
                  saveEdit()
                }
              }}
              maxLength={500}
              disabled={saving}
              placeholder="Update your comment…"
            />
            {error && (
              <div className="comment-edit-error">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-2h2zm0-4h-2V7h2z" />
                </svg>
                {error}
              </div>
            )}
            <div className="comment-edit-footer">
              <span className="comment-edit-hint d-none d-sm-inline">
                <kbd>Esc</kbd> to cancel · <kbd>Ctrl</kbd>+<kbd>Enter</kbd> to save
              </span>
              <div className="d-flex gap-2 ms-auto">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="btn btn-sm btn-light btn-pill"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveEdit}
                  className="btn btn-sm btn-share"
                  disabled={
                    saving || draft.trim().length === 0 || draft.trim() === comment.content
                  }
                >
                  {saving ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <p className="mb-1 small" style={{ wordBreak: 'break-word' }}>
              <button
                type="button"
                onClick={openProfile}
                className="btn btn-link p-0 align-baseline text-decoration-none text-dark fw-semibold me-2"
              >
                {username}
              </button>
              {comment.content}
            </p>
            <div className="d-flex align-items-center gap-3 text-secondary" style={{ fontSize: 11 }}>
              <span>{formatRelative(comment.created_at)}</span>
              {comment.updated_at && comment.updated_at !== comment.created_at && (
                <span>edited</span>
              )}
              {canEdit && (
                <button
                  type="button"
                  className="btn btn-link p-0 text-secondary"
                  style={{ fontSize: 11 }}
                  onClick={startEdit}
                  disabled={busy}
                >
                  Edit
                </button>
              )}
              {canDelete && (
                <button
                  type="button"
                  className="btn btn-link p-0 text-danger"
                  style={{ fontSize: 11 }}
                  onClick={handleDelete}
                  disabled={busy}
                >
                  Delete
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </li>
  )
}

export const CommentsSection = forwardRef(function CommentsSection({ post, readOnly = false }, ref) {
  const { user: currentUser } = useCurrentUser()
  const [comments, setComments] = useState([])
  const [skip, setSkip] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [listError, setListError] = useState('')
  const [draft, setDraft] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const inputRef = useRef(null)

  useImperativeHandle(ref, () => ({
    focusInput: () => inputRef.current?.focus(),
  }))

  const postId = post?.id
  const postOwnerId = post?.owner?.id

  const loadMore = useCallback(
    async (reset = false) => {
      if (!postId) return
      if (loading) return
      const nextSkip = reset ? 0 : skip
      setLoading(true)
      setListError('')
      try {
        const batch = await fetchComments(postId, { limit: PAGE_SIZE, skip: nextSkip })
        const arr = Array.isArray(batch) ? batch : []
        setComments((prev) => (reset ? arr : [...prev, ...arr]))
        setSkip(nextSkip + arr.length)
        if (arr.length < PAGE_SIZE) setHasMore(false)
        else setHasMore(true)
      } catch (err) {
        setListError(extractApiError(err, 'Failed to load comments'))
      } finally {
        setLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [postId, skip, loading]
  )

  useEffect(() => {
    setComments([])
    setSkip(0)
    setHasMore(true)
    loadMore(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const content = draft.trim()
    if (!content) return
    setSubmitting(true)
    setSubmitError('')
    try {
      const created = await createComment(postId, content)
      setComments((prev) => [created, ...prev])
      setSkip((n) => n + 1)
      setDraft('')
    } catch (err) {
      setSubmitError(extractApiError(err, 'Failed to post comment'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = async (commentId, content) => {
    const updated = await updateComment(commentId, content)
    setComments((prev) => prev.map((c) => (c.id === commentId ? updated : c)))
  }

  const handleDelete = async (commentId) => {
    const snapshot = comments
    setComments((prev) => prev.filter((c) => c.id !== commentId))
    setSkip((n) => Math.max(0, n - 1))
    try {
      await deleteComment(commentId)
    } catch (err) {
      setComments(snapshot)
      setListError(extractApiError(err, 'Failed to delete comment'))
    }
  }

  const canSubmit = !readOnly && currentUser && draft.trim().length > 0 && !submitting

  return (
    <section id="comments" className="bg-white px-3 py-3 comments-section">
      <h3 className="h6 fw-semibold mb-3">Comments</h3>

      {listError && (
        <div className="alert alert-danger py-2 small" role="alert">
          {listError}
        </div>
      )}

      {comments.length === 0 && !loading && !listError && (
        <p className="text-secondary small mb-3">No comments yet. Be the first to comment.</p>
      )}

      <ul className="list-unstyled mb-2">
        {comments.map((c) => {
          const isAuthor = currentUser?.id != null && c.user?.id === currentUser.id
          const isPostOwner = currentUser?.id != null && postOwnerId === currentUser.id
          return (
            <CommentRow
              key={c.id}
              comment={c}
              canEdit={isAuthor}
              canDelete={isAuthor || isPostOwner}
              onEdit={handleEdit}
              onDelete={handleDelete}
              busy={loading}
            />
          )
        })}
      </ul>

      {hasMore && (
        <div className="text-center mb-3">
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

      {!readOnly && (
        <form onSubmit={handleSubmit} className="d-flex align-items-start gap-2 border-top pt-3">
          <textarea
            ref={inputRef}
            className="form-control form-control-sm"
            rows={1}
            placeholder={currentUser ? 'Add a comment…' : 'Log in to comment'}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={!currentUser || submitting}
            maxLength={500}
            style={{ resize: 'none' }}
          />
          <button type="submit" className="btn btn-sm btn-share" disabled={!canSubmit}>
            {submitting ? 'Posting…' : 'Post'}
          </button>
        </form>
      )}
      {submitError && <div className="text-danger small mt-1">{submitError}</div>}
    </section>
  )
})
