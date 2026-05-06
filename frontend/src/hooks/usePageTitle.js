import { useEffect } from 'react'

export function usePageTitle(title) {
  useEffect(() => {
    const previous = document.title
    document.title = title ? `${title} • Instagram` : 'Instagram'
    return () => {
      document.title = previous
    }
  }, [title])
}
