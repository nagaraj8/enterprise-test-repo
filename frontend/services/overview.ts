import { Overview, SourcesResponse, request } from './client'

export async function fetchOverview() {
  return request<Overview>('/overview')
}

export async function fetchSources() {
  return request<SourcesResponse>('/sources')
}
