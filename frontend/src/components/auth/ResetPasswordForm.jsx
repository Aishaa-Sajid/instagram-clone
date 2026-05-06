import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { usePageTitle } from '@/hooks/usePageTitle'
import { resetPassword, extractApiError } from '@/api/auth'
import { AuthShell } from './AuthShell'

export function ResetPasswordForm() {
  usePageTitle('Reset password')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isLoading) return
    setError(null)
    if (password !== passwordConfirmation) {
      setError('Passwords do not match')
      return
    }
    setIsLoading(true)
    try {
      await resetPassword({ token, password, passwordConfirmation })
      navigate('/login')
    } catch (err) {
      setError(extractApiError(err, 'Could not reset password'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthShell>
      <h1 className="h3 fw-bold mb-4">Reset password</h1>

      <form onSubmit={handleSubmit} noValidate>
        {error && (
          <div className="alert alert-danger py-2" role="alert">
            {error}
          </div>
        )}
        {!token && (
          <div className="alert alert-warning py-2" role="alert">
            Missing reset token. Please use the link from your email.
          </div>
        )}

        <div className="mb-3">
          <label htmlFor="password" className="form-label fw-medium">
            New password
          </label>
          <input
            id="password"
            type="password"
            className="form-control"
            placeholder="Enter new password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading || !token}
            autoComplete="new-password"
          />
        </div>

        <div className="mb-4">
          <label htmlFor="passwordConfirmation" className="form-label fw-medium">
            Confirm password
          </label>
          <input
            id="passwordConfirmation"
            type="password"
            className="form-control"
            placeholder="Confirm new password"
            value={passwordConfirmation}
            onChange={(e) => setPasswordConfirmation(e.target.value)}
            required
            disabled={isLoading || !token}
            autoComplete="new-password"
          />
        </div>

        <button
          type="submit"
          className="btn btn-dark w-100 mb-4"
          disabled={isLoading || !token}
        >
          {isLoading ? 'Resetting...' : 'Reset password'}
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
