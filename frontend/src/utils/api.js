import axios from 'axios'

// In development Vite proxies /handshake/* → localhost:8000.
// In the Docker production build VITE_API_BASE is injected as /api/handshake
// so nginx can proxy /api/* → backend container.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/handshake',
  headers: { 'Content-Type': 'application/json' },
})

export async function startHandshake(plaintext) {
  const body = plaintext !== undefined ? { plaintext } : {}
  const { data } = await client.post('/start', body)
  return data
}

export async function advanceStep(sessionId) {
  const { data } = await client.post(`/${sessionId}/advance`)
  return data
}

export async function enableTamper(sessionId) {
  const { data } = await client.post(`/${sessionId}/tamper`)
  return data
}

export async function getFullHandshake(sessionId) {
  const { data } = await client.get(`/${sessionId}/full`)
  return data
}
