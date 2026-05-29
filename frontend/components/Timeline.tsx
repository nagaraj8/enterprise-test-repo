'use client'

import { useCallback, useEffect, useState } from 'react'
import { EventRecord } from '../services/client'
import { fetchTimeline } from '../services/timeline'

type TimelineProps = {
  source: string
  query: string
}

function formatTime(timestamp?: string | null) {
  if (!timestamp) return 'Unknown time'

  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) {
    return timestamp
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function timestampValue(timestamp?: string | null) {
  if (!timestamp) return 0

  const value = new Date(timestamp).getTime()

  return Number.isNaN(value) ? 0 : value
}

function eventIdValue(id?: number | string) {
  if (typeof id === 'number') return id

  const value = Number(id)

  return Number.isNaN(value) ? 0 : value
}

export default function Timeline({ source, query }: TimelineProps) {
  const [events, setEvents] = useState<EventRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadTimeline = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
      setError('')

      const data = await fetchTimeline({
        limit: 50,
        source,
        q: query.trim(),
      })

      setEvents(
        [...data].sort(
          (first, second) =>
            timestampValue(second.timestamp) - timestampValue(first.timestamp) ||
            eventIdValue(second.id) - eventIdValue(first.id)
        )
      )
      setLastUpdated(new Date())
    } catch (error) {
      console.error(error)
      setError('Timeline unavailable. Check the API and database connection.')
    } finally {
      setLoading(false)
    }
  }, [source, query])

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      loadTimeline()
    }, 0)

    const interval = setInterval(() => {
      loadTimeline(false)
    }, 10000)

    return () => {
      window.clearTimeout(initialLoad)
      clearInterval(interval)
    }
  }, [loadTimeline])

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-slate-500">
            Activity history
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">
            Operational timeline
          </h2>
        </div>

        <button
          type="button"
          onClick={() => loadTimeline()}
          className="h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:text-slate-950"
        >
          Refresh
        </button>
      </div>

      <div className="mt-2 text-sm text-slate-500">
        {lastUpdated
          ? `Updated ${formatTime(lastUpdated.toISOString())} / auto-refresh 10s / latest first`
          : 'Waiting for data'}
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      <div className="mt-5 space-y-3">
        {loading && (
          <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            Loading recent activity...
          </div>
        )}

        {!loading && events.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            No matching activity yet. Try another filter or ingest new events.
          </div>
        )}

        {events.map((event, index) => (
          <div
            key={`${event.id ?? index}-${event.timestamp ?? index}`}
            className="rounded-lg border border-slate-200 p-4 transition hover:border-slate-300 hover:bg-slate-50"
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold capitalize text-white">
                    {event.source || 'unknown'}
                  </span>
                  {event.event_type && (
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      {event.event_type}
                    </span>
                  )}
                </div>

                <p className="mt-3 text-sm font-semibold text-slate-950">
                  {event.action || 'Activity recorded'}
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  {[event.actor, event.target].filter(Boolean).join(' / ') || 'No actor or target captured'}
                </p>
              </div>

              <time className="shrink-0 text-sm text-slate-500">
                {formatTime(event.timestamp)}
              </time>
            </div>

            {event.summary && (
              <p className="mt-3 text-sm leading-6 text-slate-600">
                {event.summary}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
