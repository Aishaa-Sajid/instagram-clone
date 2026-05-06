import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { verifyEmail, extractApiError } from '@/api/auth'
import { AuthShell } from './AuthShell'

export function VerifyEmailForm() {
  usePageTitle('Verify email')
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const [status, setStatus] = useState(token ? 'loading' : 'missing')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    verifyEmail(token)
      .then(() => {
        if (!cancelled) setStatus('success')
      })
      .catch((err) => {
        if (cancelled) return
        setError(extractApiError(err, 'Verification failed'))
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <AuthShell>
      <h1 className="h3 fw-bold mb-4">Verify email</h1>

      {status === 'loading' && (
        <p className="text-secondary">Verifying your email...</p>
      )}
      {status === 'missing' && (
        <div className="alert alert-warning py-2" role="alert">
          Missing verification token. Please use the link from your email.
        </div>
      )}
      {status === 'success' && (
        <div className="alert alert-success py-2" role="alert">
          Email verified. You can log in now.
        </div>
      )}
      {status === 'error' && (
        <div className="alert alert-danger py-2" role="alert">
          {error}
        </div>
      )}

      <div className="text-center text-secondary small mt-4">
        <Link to="/login" className="text-dark fw-semibold text-decoration-none">
          Back to log in
        </Link>
      </div>
    </AuthShell>
  )
}
