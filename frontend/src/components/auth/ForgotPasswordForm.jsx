import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { requestPasswordReset, extractApiError } from '@/api/auth'
import { AuthShell } from './AuthShell'

export function ForgotPasswordForm() {
  usePageTitle('Forgot password')
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isLoading) return
    setError(null)
    setIsLoading(true)
    try {
      await requestPasswordReset({ email })
      setSent(true)
    } catch (err) {
      setError(extractApiError(err, 'Could not send reset email'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthShell>
      <h1 className="h3 fw-bold mb-2">Forgot password</h1>
      <p className="text-secondary small mb-4">
        Enter the email for your account and we&apos;ll send you a reset link.
      </p>

      <form onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="alert alert-danger py-2" role="alert">
            {error}
          </div>
        )}
        {sent && (
          <div className="alert alert-success py-2" role="alert">
            If that email exists, a reset link is on its way.
          </div>
        )}

        <div className="mb-3">
          <label htmlFor="email" className="form-label fw-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="form-control"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="email"
          />
        </div>

        <button type="submit" className="btn btn-dark w-100 mb-4" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>

      <div className="text-center text-secondary small">
        <Link to="/login" className="text-dark fw-semibold text-decoration-none">
          Back to log in
        </Link>
      </div>
    </AuthShell>
  )
}
