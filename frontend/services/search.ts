import { SearchResult, request } from './client'

export async function semanticSearch(
  query: string,
  source = 'all',
  limit = 8
) {
  return request<SearchResult[]>('/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      source: source === 'all' ? undefined : source,
      limit,
    }),
  })
}
