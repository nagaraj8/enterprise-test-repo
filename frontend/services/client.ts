const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export type EventRecord = {
  id?: number | string
  source: string
  actor?: string | null
  action?: string | null
  target?: string | null
  event_type?: string | null
  service_name?: string | null
  environment?: string | null
  severity?: string | null
  fingerprint?: string | null
  timestamp?: string | null
  ingested_at?: string | null
  summary?: string | null
}

export type SearchResult = EventRecord & {
  score: number
}

export type SourceStat = {
  source: string
  count: number
}

export type Overview = {
  total_events: number
  events_last_24h: number
  open_incidents?: number
  services?: number
  deployments_last_24h?: number
  latest_event_timestamp?: string | null
  sources: SourceStat[]
}

export type SourcesResponse = {
  sources: string[]
}

export type AskResponse = {
  answer: string
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      query.set(key, String(value))
    }
  })

  const queryString = query.toString()

  return queryString ? `?${queryString}` : ''
}

export { request }
