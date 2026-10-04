// Vite substitutes this at build time; the URL is used by the user's browser.
export const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')
  .trim()
  .replace(/\/+$/, '')
