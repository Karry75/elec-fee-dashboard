import axios from 'axios'

// All API calls go through /api (proxied to Flask in dev, same-origin in prod).
const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Admin token is read from localStorage if present (set via a dev/login step).
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers['X-Admin-Token'] = token
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.data && err.response.data.message) {
      err.message = err.response.data.message
    }
    return Promise.reject(err)
  }
)

export default client
