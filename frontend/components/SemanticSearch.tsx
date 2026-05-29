'use client'

import { useState } from 'react'

import { semanticSearch }
from '../services/search'

export default function SemanticSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])

  const handleSearch = async () => {
    const data = await semanticSearch(query)

    setResults(data)
  }

  return (
    <div className="mt-10">
      <h2 className="text-3xl font-bold mb-4">
        Semantic Incident Search
      </h2>

      <div className="flex gap-4">
        <input
          value={query}
          onChange={(e) =>
            setQuery(e.target.value)
          }
          placeholder="Find similar incidents..."
          className="flex-1 p-4 rounded-xl bg-gray-900 border border-gray-700"
        />

        <button
          onClick={handleSearch}
          className="bg-white text-black px-6 rounded-xl"
        >
          Search
        </button>
      </div>

      <div className="mt-6 space-y-4">
        {results.map((result: any, index) => (
          <div
            key={index}
            className="bg-gray-900 p-5 rounded-2xl"
          >
            <p>
              <strong>Source:</strong> {result.source}
            </p>

            <p>
              <strong>Actor:</strong> {result.actor}
            </p>

            <p>
              <strong>Action:</strong> {result.action}
            </p>

            <p>
              <strong>Target:</strong> {result.target}
            </p>

            <p>
              <strong>Similarity:</strong>{' '}
              {result.score.toFixed(3)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}