'use client'

import { useEffect, useMemo, useState } from 'react'
import AIQueryBox from '../components/AIQueryBox'
import Timeline from '../components/Timeline'
import SemanticSearch from '../components/SemanticSearch'
import { Overview } from '../services/client'
import { fetchOverview, fetchSources } from '../services/overview'

const sources = ['all', 'github', 'slack', 'incident', 'deploy']

function formatCount(value?: number) {
  return new Intl.NumberFormat('en').format(value ?? 0)
}

function formatLatest(timestamp?: string | null, totalEvents = 0) {
  if (!timestamp) return totalEvents > 0 ? 'Timestamp missing' : 'No events'

  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) return timestamp

  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default function HomePage() {
  const [source, setSource] = useState('all')
  const [query, setQuery] = useState('')
  const [overview, setOverview] = useState<Overview | null>(null)
  const [dynamicSources, setDynamicSources] = useState<string[]>(sources)
  const [overviewError, setOverviewError] = useState('')

  const availableSources = useMemo(
    () => Array.from(new Set(['all', ...dynamicSources.filter((item) => item !== 'all')])),
    [dynamicSources]
  )

  useEffect(() => {
    let cancelled = false

    async function loadOverview() {
      try {
        const [overviewData, sourceData] = await Promise.all([
          fetchOverview(),
          fetchSources(),
        ])

        if (cancelled) return

        setOverview(overviewData)
        setDynamicSources(
          sourceData.sources.length > 0
            ? ['all', ...sourceData.sources]
            : sources
        )
        setOverviewError('')
      } catch (error) {
        console.error(error)

        if (!cancelled) {
          setOverviewError('Backend metrics unavailable')
        }
      }
    }

    loadOverview()

    const interval = window.setInterval(loadOverview, 15000)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  const topSource = overview?.sources[0]

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="grid gap-5 border-b border-slate-200 pb-6 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="text-sm font-semibold uppercase text-emerald-700">
              Enterprise AI operations
            </p>
            <h1 className="mt-2 text-4xl font-semibold text-slate-950 sm:text-5xl">
              Enterprise Decision Brain
            </h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
              Search operational activity, inspect history, and ask AI questions with incident context in one focused console.
            </p>
          </div>

          <div className="grid gap-2 sm:min-w-96 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium text-slate-500">Events</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatCount(overview?.total_events)}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium text-slate-500">Last 24h</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatCount(overview?.events_last_24h)}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium text-slate-500">Latest</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatLatest(
                  overview?.latest_event_timestamp,
                  overview?.total_events
                )}
              </p>
            </div>
          </div>
        </header>

        <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_auto] md:items-center">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${overviewError ? 'bg-amber-500' : 'bg-emerald-500'}`} />
            <p className="text-sm font-semibold text-slate-800">
              {overviewError || 'Operational data connected'}
            </p>
            {topSource && (
              <p className="text-sm text-slate-500">
                Top source: {topSource.source} / {formatCount(topSource.count)} events
              </p>
            )}
          </div>

          <p className="text-sm text-slate-500">
            Sources: {Math.max(availableSources.length - 1, 0)}
          </p>
        </section>

        <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[1fr_auto] lg:items-end">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700">
              Filter history
            </span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter by service, actor, action, target, or source"
              className="mt-2 h-11 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 text-sm outline-none transition focus:border-slate-900 focus:bg-white"
            />
          </label>

          <div>
            <p className="text-sm font-semibold text-slate-700">Source</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {availableSources.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setSource(option)}
                  className={`h-11 rounded-lg border px-4 text-sm font-semibold capitalize transition ${
                    source === option
                      ? 'border-slate-950 bg-slate-950 text-white'
                      : 'border-slate-300 bg-white text-slate-700 hover:border-slate-500'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </section>

        <AIQueryBox />

        <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <Timeline source={source} query={query} />
          <SemanticSearch source={source} />
        </div>
      </div>
    </main>
  )
}
