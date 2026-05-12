import { Link, useLocation, useNavigate } from 'react-router-dom'
import logoSvg from '@/assets/logo.svg'
import { CurrentUserChip } from '@/components/feed/CurrentUserChip'

export function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const showBack = location.pathname !== '/'

  return (
    <header className="feed-header">
      <div className="feed-header-inner container-md d-flex align-items-center gap-2 px-3 px-md-4">
        {showBack && (
          <button
            type="button"
            onClick={() => navigate(-1)}
            aria-label="Back"
            className="icon-btn"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
            </svg>
          </button>
        )}
        <Link
          to="/"
          className="d-flex align-items-center gap-2 text-decoration-none"
          aria-label="Instagram home"
        >
          <img src={logoSvg} alt="Instagram" width="26" height="26" />
          <span className="font-display gradient-text">Instagram</span>
        </Link>
        <div className="ms-auto">
          <CurrentUserChip />
        </div>
      </div>
    </header>
  )
}
