import { useEffect, useRef, useState } from 'react'
import { createPost } from '@/api/posts'
import { extractApiError } from '@/api/auth'

const MAX_IMAGES = 10
const MAX_FILE_SIZE = 5 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function CreatePostForm({ onCreated }) {
  const [open, setOpen] = useState(false)
  const [caption, setCaption] = useState('')
  const [files, setFiles] = useState([])
  const [previews, setPreviews] = useState([])
  const [dragOver, setDragOver] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f))
    setPreviews(urls)
    return () => urls.forEach((u) => URL.revokeObjectURL(u))
  }, [files])

  const validateAndAdd = (incoming) => {
    setError('')
    const arr = Array.from(incoming)
    const valid = []
    for (const file of arr) {
      if (!ALLOWED_TYPES.includes(file.type)) {
        setError(`${file.name}: only JPEG, PNG, or WEBP allowed`)
        continue
      }
      if (file.size > MAX_FILE_SIZE) {
        setError(`${file.name}: exceeds 5MB`)
        continue
      }
      valid.push(file)
    }
    setFiles((prev) => {
      const merged = [...prev, ...valid].slice(0, MAX_IMAGES)
      if (prev.length + valid.length > MAX_IMAGES) {
        setError(`Max ${MAX_IMAGES} images allowed`)
      }
      return merged
    })
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files?.length) validateAndAdd(e.dataTransfer.files)
  }

  const removeAt = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const reset = () => {
    setCaption('')
    setFiles([])
    setError('')
    setOpen(false)
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (files.length === 0) {
      setError('Add at least one image')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const created = await createPost({ caption, files })
      onCreated?.(created)
      reset()
    } catch (err) {
      setError(extractApiError(err, 'Failed to create post'))
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="create-post-trigger w-100 bg-white d-flex align-items-center gap-3 px-3 py-3 mb-3 mb-sm-4"
      >
        <span
          className="rounded-circle d-flex align-items-center justify-content-center text-white flex-shrink-0"
          style={{
            width: 42,
            height: 42,
            background:
              'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
            boxShadow: '0 2px 8px rgba(220, 39, 67, 0.25)',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </span>
        <span className="text-secondary flex-grow-1 text-start">Share a new post…</span>
      </button>
    )
  }

  return (
    <form
      onSubmit={onSubmit}
      className="bg-white mb-3 mb-sm-4 overflow-hidden create-post-card"
    >
      <header className="d-flex align-items-center px-3 py-2 border-bottom">
        <h2 className="h6 mb-0 fw-semibold flex-grow-1">Create new post</h2>
        <button
          type="button"
          onClick={reset}
          aria-label="Cancel"
          className="icon-btn"
          disabled={submitting}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </header>

      <div className="p-3">
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
          }}
          className={`dropzone d-flex flex-column align-items-center justify-content-center text-center p-4 mb-3 ${
            dragOver ? 'dropzone-active' : ''
          }`}
        >
          <span className="dropzone-icon mb-3">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          </span>
          <div className="fw-semibold mb-1">Drag photos here</div>
          <div className="text-secondary small mb-3">or click to browse</div>
          <span className="btn-share btn-sm">Select from device</span>
          <div className="text-secondary mt-3" style={{ fontSize: 11 }}>
            JPEG · PNG · WEBP — up to {MAX_IMAGES} images, 5MB each
          </div>
          <input
            ref={inputRef}
            type="file"
            accept={ALLOWED_TYPES.join(',')}
            multiple
            hidden
            onChange={(e) => {
              if (e.target.files?.length) validateAndAdd(e.target.files)
              e.target.value = ''
            }}
          />
        </div>

        {previews.length > 0 && (
          <div className="d-flex flex-wrap gap-2 mb-3">
            {previews.map((src, idx) => (
              <div key={src} className="preview-tile position-relative">
                <img src={src} alt="" className="preview-img" />
                <button
                  type="button"
                  onClick={() => removeAt(idx)}
                  aria-label="Remove image"
                  className="preview-remove"
                  disabled={submitting}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        <textarea
          className="form-control caption-input"
          rows={3}
          placeholder="Write a caption…"
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          disabled={submitting}
          maxLength={2200}
          style={{ resize: 'none' }}
        />

        {error && (
          <div className="alert alert-danger py-2 small mb-0 mt-2" role="alert">
            {error}
          </div>
        )}
      </div>

      <footer className="d-flex align-items-center gap-2 px-3 py-2 border-top">
        <span className="text-secondary small flex-grow-1">
          {files.length} / {MAX_IMAGES} selected
        </span>
        <button
          type="button"
          onClick={reset}
          className="btn btn-sm btn-light btn-pill"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-sm btn-share"
          disabled={submitting || files.length === 0}
        >
          {submitting ? 'Sharing…' : 'Share'}
        </button>
      </footer>
    </form>
  )
}
