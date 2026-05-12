import { useEffect, useRef, useState } from 'react'
import { updatePost } from '@/api/posts'
import { extractApiError } from '@/api/auth'

const MAX_IMAGES = 10
const MAX_FILE_SIZE = 5 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function EditPostForm({ post, onCancel, onUpdated }) {
  const [caption, setCaption] = useState(post.caption ?? '')
  const [existingImages, setExistingImages] = useState(post.images ?? [])
  const [imagesToDelete, setImagesToDelete] = useState([])
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

  const remainingExisting = existingImages.filter((img) => !imagesToDelete.includes(img.id))
  const totalCount = remainingExisting.length + files.length

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
      const room = MAX_IMAGES - remainingExisting.length - prev.length
      if (valid.length > room) {
        setError(`Max ${MAX_IMAGES} images allowed`)
      }
      return [...prev, ...valid].slice(0, MAX_IMAGES - remainingExisting.length)
    })
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files?.length) validateAndAdd(e.dataTransfer.files)
  }

  const toggleDeleteExisting = (imageId) => {
    setImagesToDelete((prev) =>
      prev.includes(imageId) ? prev.filter((x) => x !== imageId) : [...prev, imageId]
    )
  }

  const removeNewAt = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (totalCount === 0) {
      setError('At least one image is required')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const updated = await updatePost(post.id, {
        caption,
        files,
        imagesToDelete,
      })
      onUpdated?.(updated)
    } catch (err) {
      setError(extractApiError(err, 'Failed to update post'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="bg-white overflow-hidden create-post-card">
      <header className="d-flex align-items-center px-3 py-2 border-bottom">
        <h2 className="h6 mb-0 fw-semibold flex-grow-1">Edit post</h2>
        <button
          type="button"
          onClick={onCancel}
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
        {existingImages.length > 0 && (
          <div className="d-flex flex-wrap gap-2 mb-3">
            {existingImages.map((img) => {
              const marked = imagesToDelete.includes(img.id)
              return (
                <div
                  key={img.id}
                  className="preview-tile position-relative"
                  style={{ opacity: marked ? 0.4 : 1 }}
                >
                  <img src={img.image_url} alt="" className="preview-img" />
                  <button
                    type="button"
                    onClick={() => toggleDeleteExisting(img.id)}
                    aria-label={marked ? 'Keep image' : 'Remove image'}
                    title={marked ? 'Undo remove' : 'Remove'}
                    className="preview-remove"
                    disabled={submitting}
                  >
                    {marked ? (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="3 11 9 17 21 5" />
                      </svg>
                    ) : (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    )}
                  </button>
                </div>
              )
            })}
            {previews.map((src, idx) => (
              <div key={src} className="preview-tile position-relative">
                <img src={src} alt="" className="preview-img" />
                <span
                  className="position-absolute top-0 start-0 m-1 px-1 small text-white"
                  style={{ background: 'rgba(0,0,0,0.55)', borderRadius: 4, fontSize: 10 }}
                >
                  NEW
                </span>
                <button
                  type="button"
                  onClick={() => removeNewAt(idx)}
                  aria-label="Remove new image"
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

        {totalCount < MAX_IMAGES && (
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
            <div className="fw-semibold mb-1">Add more photos</div>
            <div className="text-secondary small mb-3">drag or click to browse</div>
            <span className="btn-share btn-sm">Select from device</span>
            <div className="text-secondary mt-3" style={{ fontSize: 11 }}>
              JPEG · PNG · WEBP — up to {MAX_IMAGES} total, 5MB each
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
          {totalCount} / {MAX_IMAGES} images
        </span>
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-sm btn-light btn-pill"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-sm btn-share"
          disabled={submitting || totalCount === 0}
        >
          {submitting ? 'Saving…' : 'Save'}
        </button>
      </footer>
    </form>
  )
}
