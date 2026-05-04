import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../lib/auth'

const FacebookIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="white" aria-hidden="true">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
  </svg>
)

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (submitting) return
    setSubmitting(true)
    setError('')
    try {
      await login(form)
      navigate('/')
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Invalid credentials.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex justify-center">
      <div className="w-full max-w-[360px] px-8 pt-16">
        <h1
          className="text-center text-[44px] leading-none text-black mb-12"
          style={{
            fontFamily:
              '"Grand Hotel", "Billabong", "Snell Roundhand", cursive',
          }}
        >
          Instagram
        </h1>

        <button
          type="button"
          className="w-full bg-[#1877F2] hover:bg-[#1668d8] text-white font-semibold rounded-md py-2.5 flex items-center justify-center gap-2 text-[15px]"
        >
          <FacebookIcon />
          Continue with Facebook
        </button>

        <div className="flex items-center w-full my-6">
          <div className="flex-1 h-px bg-[#DBDBDB]" />
          <span className="px-4 text-sm text-[#8E8E8E] uppercase">OR</span>
          <div className="flex-1 h-px bg-[#DBDBDB]" />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <input
            name="email"
            type="text"
            value={form.email}
            onChange={handleChange}
            placeholder="phone number,username, or email"
            autoComplete="username"
            className="w-full bg-[#EFEFEF] rounded-md px-3 py-2.5 text-sm text-black placeholder:text-[#8E8E8E] outline-none focus:bg-[#E8E8E8]"
          />
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="password"
            autoComplete="current-password"
            className="w-full bg-[#EFEFEF] rounded-md px-3 py-2.5 text-sm text-black placeholder:text-[#8E8E8E] outline-none focus:bg-[#E8E8E8]"
          />

          <div className="flex justify-end mt-1">
            <Link
              to="/accounts/password/reset"
              className="text-[13px] text-[#1877F2] font-semibold hover:underline"
            >
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="mt-4 w-full rounded-md bg-[#B2DFFC] hover:bg-[#9CD3FB] text-white font-semibold py-2.5 text-[15px] transition-colors disabled:opacity-70"
          >
            {submitting ? 'Logging in...' : 'Log In'}
          </button>

          {error && (
            <p className="text-[#ED4956] text-sm text-center mt-2">{error}</p>
          )}
        </form>

        <p className="text-center text-sm text-[#8E8E8E] mt-6">
          Don't have an account?{' '}
          <Link
            to="/accounts/emailsignup"
            className="text-[#1877F2] font-semibold hover:underline"
          >
            sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
