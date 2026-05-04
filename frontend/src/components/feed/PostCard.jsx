import { useState } from 'react'

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

export function PostCard({ post }) {
  const images = post.images ?? []
  const [index, setIndex] = useState(0)
  const [liked, setLiked] = useState(false)
  const [saved, setSaved] = useState(false)

  const owner = post.owner ?? {}
  const username = owner.username ?? 'unknown'
  const avatarLetter = username.charAt(0).toUpperCase()

  const next = () => setIndex((i) => Math.min(i + 1, images.length - 1))
  const prev = () => setIndex((i) => Math.max(i - 1, 0))

  return (
    <article className="bg-white border rounded-3 mb-4 overflow-hidden post-card">
      <header className="d-flex align-items-center gap-2 px-3 py-2">
        <div
          className="rounded-circle d-flex align-items-center justify-content-center text-white fw-semibold"
          style={{
            width: 36,
            height: 36,
            background:
              'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
          }}
        >
          <span
            className="rounded-circle bg-white text-dark d-flex align-items-center justify-content-center"
            style={{ width: 30, height: 30, fontSize: 14 }}
          >
            {avatarLetter}
          </span>
        </div>
        <div className="flex-grow-1">
          <div className="fw-semibold small">{username}</div>
        </div>
        <button className="btn btn-sm btn-link text-dark p-0" aria-label="More options">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="12" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="19" cy="12" r="2" />
          </svg>
        </button>
      </header>

      <div className="post-media position-relative bg-black">
        {images.length > 0 ? (
          <>
            <img
              src={images[index].image_url}
              alt={post.caption ?? 'post image'}
              className="w-100 d-block post-image"
              loading="lazy"
            />
            {images.length > 1 && (
              <>
                {index > 0 && (
                  <button
                    type="button"
                    onClick={prev}
                    aria-label="Previous image"
                    className="post-nav-btn position-absolute top-50 start-0 translate-middle-y ms-2"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
                    </svg>
                  </button>
                )}
                {index < images.length - 1 && (
                  <button
                    type="button"
                    onClick={next}
                    aria-label="Next image"
                    className="post-nav-btn position-absolute top-50 end-0 translate-middle-y me-2"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M8.59 16.59 10 18l6-6-6-6-1.41 1.41L13.17 12z" />
                    </svg>
                  </button>
                )}
                <div className="position-absolute bottom-0 start-50 translate-middle-x mb-2 d-flex gap-1">
                  {images.map((_, i) => (
                    <span
                      key={i}
                      className={`post-dot ${i === index ? 'post-dot-active' : ''}`}
                    />
                  ))}
                </div>
              </>
            )}
          </>
        ) : (
          <div
            className="d-flex align-items-center justify-content-center text-secondary"
            style={{ height: 320 }}
          >
            No image
          </div>
        )}
      </div>

      <div className="px-3 pt-2 pb-1 d-flex align-items-center gap-3">
        <button
          type="button"
          onClick={() => setLiked((v) => !v)}
          aria-label={liked ? 'Unlike' : 'Like'}
          className="btn btn-link p-0 text-dark post-action-btn"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill={liked ? '#ed4956' : 'none'}
            stroke={liked ? '#ed4956' : 'currentColor'}
            strokeWidth="2"
          >
            <path d="M12 21s-7.5-4.6-9.5-9.3C1.2 8.6 3 5 6.5 5 8.6 5 10.5 6.2 12 8c1.5-1.8 3.4-3 5.5-3C21 5 22.8 8.6 21.5 11.7 19.5 16.4 12 21 12 21z" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Comment"
          className="btn btn-link p-0 text-dark post-action-btn"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Share"
          className="btn btn-link p-0 text-dark post-action-btn"
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
        <button
          type="button"
          onClick={() => setSaved((v) => !v)}
          aria-label={saved ? 'Unsave' : 'Save'}
          className="btn btn-link p-0 text-dark ms-auto post-action-btn"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill={saved ? 'currentColor' : 'none'}
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      </div>

      <div className="px-3 pb-3">
        {post.caption && (
          <p className="mb-1 small">
            <span className="fw-semibold me-2">{username}</span>
            {post.caption}
          </p>
        )}
        <div className="text-secondary text-uppercase" style={{ fontSize: 10, letterSpacing: 0.4 }}>
          {formatRelative(post.created_at)}
        </div>
      </div>
    </article>
  )
}
