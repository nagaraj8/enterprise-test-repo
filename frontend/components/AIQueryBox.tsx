'use client'

import { useState } from 'react'
import { askQuestion } from '../services/api'

const suggestions = [
  'What changed before the latest payment incident?',
  'Summarize risky activity in the last 24 hours',
  'Which GitHub events look related to Slack alerts?',
]

export default function AIQueryBox() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAsk = async () => {
    const trimmedQuestion = question.trim()

    if (!trimmedQuestion || loading) return

    try {
      setLoading(true)
      setError('')

      const data = await askQuestion(trimmedQuestion)

      setAnswer(data.answer)
    } catch (error) {
      console.error(error)
      setError('The AI service could not answer right now. Check the backend connection and API key.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-slate-500">
            AI reasoning
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">
            Ask across operational history
          </h2>
        </div>
        <span className="self-start rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          Context aware
        </span>
      </div>

      <div className="mt-5 flex flex-col gap-3 lg:flex-row">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
              handleAsk()
            }
          }}
          placeholder="Why did payment-service fail yesterday?"
          className="min-h-28 flex-1 resize-none rounded-lg border border-slate-300 bg-slate-50 p-4 text-sm text-slate-950 outline-none transition focus:border-slate-900 focus:bg-white"
        />

        <button
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="h-12 rounded-lg bg-slate-950 px-6 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300 lg:h-auto"
        >
          {loading ? 'Thinking...' : 'Ask AI'}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setQuestion(suggestion)}
            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-slate-400 hover:text-slate-950"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      {answer && (
        <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-semibold text-slate-950">
            AI response
          </h3>

          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
            {answer}
          </p>
        </div>
      )}
    </section>
  )
}
