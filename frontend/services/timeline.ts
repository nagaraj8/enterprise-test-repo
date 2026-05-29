export async function fetchTimeline() {
  const response = await fetch(
    'http://localhost:8000/timeline'
  )

  return response.json()
}