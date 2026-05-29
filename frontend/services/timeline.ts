import { EventRecord, buildQuery, request } from './client'

export type TimelineFilters = {
  limit?: number
  source?: string
  q?: string
}

export async function fetchTimeline(filters: TimelineFilters = {}) {
  const source =
    filters.source && filters.source !== 'all' ? filters.source : undefined

  return request<EventRecord[]>(
    `/timeline${buildQuery({
      limit: filters.limit ?? 50,
      source,
      q: filters.q,
    })}`
  )
}
