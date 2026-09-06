import axios from 'axios'

export const API_URL = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000'
).replace(/\/$/, '')

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120s timeout for deep multi-agent validation
})

export async function chatWithVentureIQ(sessionId, message) {
  try {
    const response = await api.post('/chat', {
      session_id: sessionId,
      message,
    })
    return response.data
  } catch (error) {
    console.error('VentureIQ /chat error:', error)
    if (error.code === 'ECONNABORTED') {
      throw new Error('The request timed out. Please try again.')
    }
    if (!error.response) {
      throw new Error('Unable to connect to the VentureIQ backend server at ' + API_URL)
    }
    const status = error.response.status
    const detail = error.response.data?.detail
    if (status === 400 || status === 422) {
      throw new Error(detail || 'Invalid request parameters.')
    }
    if (status === 429) {
      throw new Error('A request is already in progress. Please wait a moment.')
    }
    throw new Error(detail || 'The conversational supervisor is temporarily unavailable.')
  }
}

export async function analyzeStartup(query, sessionId) {
  try {
    const response = await api.post('/analyze', {
      startup_idea: query,
      session_id: sessionId,
    })
    return response.data
  } catch (error) {
    console.error('VentureIQ /analyze error:', error)
    if (error.code === 'ECONNABORTED') {
      throw new Error('Validation analysis timed out. Please try again.')
    }
    if (!error.response) {
      throw new Error('Unable to connect to the VentureIQ backend server at ' + API_URL)
    }
    const status = error.response.status
    const detail = error.response.data?.detail
    if (status === 429) {
      throw new Error('An analysis is already running for this startup idea.')
    }
    throw new Error(detail || 'Unable to complete the multi-agent startup validation.')
  }
}

export async function getBackendStats() {
  try {
    const response = await api.get('/stats')
    return response.data
  } catch {
    return null
  }
}