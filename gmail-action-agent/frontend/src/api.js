const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { message: text }
    }
  }

  if (!res.ok) {
    const detail = data?.detail || data?.message || res.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return data
}

export function getHealth() {
  return request('/health')
}

export function getStatus() {
  return request('/status')
}

export function getAuthUrl() {
  return request('/auth/url')
}

export function scanInbox(body = {}) {
  return request('/scan', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getNotifications(includeClosed = false) {
  const q = includeClosed ? '?include_closed=true' : ''
  return request(`/notifications${q}`)
}

export function dismissNotification(id) {
  return request(`/notifications/${encodeURIComponent(id)}/dismiss`, {
    method: 'POST',
  })
}

export function completeNotification(id) {
  return request(`/notifications/${encodeURIComponent(id)}/complete`, {
    method: 'POST',
  })
}

export function getAgents() {
  return request('/agents')
}

export function getPipelineLog() {
  return request('/pipeline/log')
}
