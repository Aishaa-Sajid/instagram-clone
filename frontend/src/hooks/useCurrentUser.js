import { useEffect, useState } from 'react'
import { getCurrentUser } from '@/api/auth'

let cached = null
let inflight = null
const subscribers = new Set()

function notify() {
  for (const fn of subscribers) fn(cached)
}

export function clearCurrentUserCache() {
  cached = null
  inflight = null
  notify()
}

export function setCurrentUserCache(user) {
  cached = user
  notify()
}

export function useCurrentUser() {
  const [user, setUser] = useState(cached)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(!cached)

  useEffect(() => {
    subscribers.add(setUser)
    return () => {
      subscribers.delete(setUser)
    }
  }, [])

  useEffect(() => {
    if (cached) {
      setUser(cached)
      setLoading(false)
      return
    }
    let cancelled = false
    if (!inflight) inflight = getCurrentUser()
    inflight
      .then((data) => {
        cached = data
        notify()
        if (!cancelled) setLoading(false)
      })
      .catch((err) => {
        inflight = null
        if (!cancelled) {
          setError(err)
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { user, loading, error }
}
