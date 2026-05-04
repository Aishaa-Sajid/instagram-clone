import logoSvg from '@/assets/logo.svg'

export function AuthShell({ children }) {
  return (
    <div className="d-flex flex-column min-vh-100">
      <header
        className="d-flex align-items-center bg-white border-bottom px-3 px-md-5"
        style={{ height: '56px' }}
      >
        <div className="d-flex align-items-center gap-2">
          <img src={logoSvg} alt="Instagram" width="24" height="24" />
          <span className="font-display">Instagram</span>
        </div>
      </header>

      <main className="flex-grow-1 d-flex align-items-center justify-content-center p-3 p-md-5">
        <div className="auth-card bg-white border rounded p-4 p-md-5">{children}</div>
      </main>

      <footer className="d-flex flex-column flex-sm-row align-items-start align-items-sm-center gap-2 gap-sm-3 bg-white border-top px-3 px-md-5 py-3 py-md-4">
        <div className="d-flex align-items-center gap-2">
          <img src={logoSvg} alt="Instagram" width="24" height="24" />
          <span className="font-display">Instagram</span>
        </div>
        <span className="text-secondary small">
          &copy; {new Date().getFullYear()} Instagram Clone. All rights reserved.
        </span>
      </footer>
    </div>
  )
}
