'use client'

import { useState } from 'react'
import { SearchResult } from '../services/client'
import { semanticSearch } from '../services/search'

type SemanticSearchProps = {
  source: string
}

function formatScore(score: number) {
  return `${Math.round(score * 100)}%`
}

export default function SemanticSearch({ source }: SemanticSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    const trimmedQuery = query.trim()

    if (!trimmedQuery || loading) return

    try {
      setLoading(true)
      setError('')

      const data = await semanticSearch(trimmedQuery, source)

      setResults(data)
    } catch (error) {
      console.error(error)
      setError('Search failed. Confirm embeddings exist and the backend is running.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-slate-500">
            Semantic search
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">
            Find related activity
          </h2>
        </div>
        <p className="text-sm text-slate-500">
          Filter: {source === 'all' ? 'all sources' : source}
        </p>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              handleSearch()
            }
          }}
          placeholder="Find similar incidents..."
          className="h-12 flex-1 rounded-lg border border-slate-300 bg-slate-50 px-4 text-sm text-slate-950 outline-none transition focus:border-slate-900 focus:bg-white"
        />

        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="h-12 rounded-lg bg-slate-950 px-6 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      <div className="mt-5 space-y-3">
        {!loading && results.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            Search by service, error text, actor, deployment, or incident symptom.
          </div>
        )}

        {results.map((result, index) => (
          <div
            key={`${result.id ?? index}-${result.timestamp ?? index}`}
            className="rounded-lg border border-slate-200 p-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold capitalize text-slate-950">
                  {result.source}
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  {[result.actor, result.action, result.target]
                    .filter(Boolean)
                    .join(' / ')}
                </p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {formatScore(result.score)}
              </span>
            </div>

            {result.summary && (
              <p className="mt-3 text-sm leading-6 text-slate-600">
                {result.summary}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
