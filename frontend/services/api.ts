import { AskResponse, request } from './client'

export async function askQuestion(query: string) {
  return request<AskResponse>('/query', {
    method: 'POST',
    body: JSON.stringify({ query }),
  })
}
