export async function semanticSearch(
  query: string
) {
  const response = await fetch(
    'http://localhost:8000/search',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    }
  )

  return response.json()
}