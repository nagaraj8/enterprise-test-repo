"use client"

import { useEffect, useMemo, useState } from "react"

import IncidentCard from "./IncidentCard"

import {
  fetchIncidentDetails,
  fetchIncidents,
  runCorrelation,
  summarizeIncident,
} from "../../services/incident"

import {
  Incident,
  IncidentDetails,
} from "../../types/incident"

function formatTime(timestamp?: string | null) {
  if (!timestamp) return 'No timestamp'

  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) return timestamp

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function severityRank(severity?: string) {
  return {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  }[severity?.toLowerCase() ?? 'medium'] ?? 2
}

export default function IncidentPanel() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [details, setDetails] = useState<IncidentDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [error, setError] = useState('')

  const sortedIncidents = useMemo(
    () =>
      [...incidents].sort(
        (first, second) =>
          severityRank(second.severity) - severityRank(first.severity) ||
          (second.risk_score ?? 0) - (first.risk_score ?? 0)
      ),
    [incidents]
  )

  async function loadIncidents(nextSelectedId?: number | null) {
    try {
      const data = await fetchIncidents()
      const nextIncidents = data.incidents || []
      const resolvedSelectedId =
        nextSelectedId ??
        selectedId ??
        nextIncidents[0]?.id ??
        null

      setIncidents(nextIncidents)
      setSelectedId(resolvedSelectedId)
      setError('')
    } catch (error) {
      console.error(error)
      setError('Incidents unavailable. Confirm the backend and database are running.')
    }
  }

  async function handleCorrelation() {
    try {
      setLoading(true)
      setError('')

      await runCorrelation()
      await loadIncidents(null)
    } catch (error) {
      console.error(error)
      setError('Correlation failed. Check recent event data and database schema.')
    } finally {
      setLoading(false)
    }
  }

  async function handleSummarize() {
    if (!selectedId) return

    try {
      setSummaryLoading(true)
      const summary = await summarizeIncident(selectedId)

      setDetails((current) => {
        if (!current) return current

        return {
          ...current,
          incident: {
            ...current.incident,
            ai_summary: summary.ai_summary,
            risk_score: summary.risk_score,
          },
        }
      })
    } catch (error) {
      console.error(error)
      setError('Summary refresh failed.')
    } finally {
      setSummaryLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      async function loadInitialIncidents() {
        try {
          const data = await fetchIncidents()
          const nextIncidents = data.incidents || []

          setIncidents(nextIncidents)
          setSelectedId(nextIncidents[0]?.id ?? null)
          setError('')
        } catch (error) {
          console.error(error)
          setError('Incidents unavailable. Confirm the backend and database are running.')
        }
      }

      loadInitialIncidents()
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [])

  useEffect(() => {
    if (!selectedId) {
      return
    }

    let cancelled = false

    async function loadDetails() {
      try {
        setDetailsLoading(true)
        const data = await fetchIncidentDetails(selectedId as number)

        if (!cancelled) {
          setDetails(data)
        }
      } catch (error) {
        console.error(error)

        if (!cancelled) {
          setError('Incident details unavailable.')
        }
      } finally {
        if (!cancelled) {
          setDetailsLoading(false)
        }
      }
    }

    loadDetails()

    return () => {
      cancelled = true
    }
  }, [selectedId])

  const selectedDetails =
    details?.incident.id === selectedId ? details : null
  const selectedIncident = selectedDetails?.incident ?? null

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-slate-500">
            Incident command
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">
            Active incidents
          </h2>
        </div>

        <button
          onClick={handleCorrelation}
          disabled={loading}
          className="h-10 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? 'Correlating...' : 'Run correlation'}
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      <div className={`mt-5 grid gap-5 ${sortedIncidents.length > 0 ? 'xl:grid-cols-[0.85fr_1.15fr]' : ''}`}>
        <div className="space-y-3">
          {sortedIncidents.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
              No correlated incidents yet.
            </div>
          )}

          {sortedIncidents.map((incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              active={incident.id === selectedId}
              onSelect={(nextIncident) => setSelectedId(nextIncident.id)}
            />
          ))}
        </div>

        {sortedIncidents.length > 0 && (
        <div className="min-h-96 rounded-lg border border-slate-200 bg-slate-50 p-4">
          {detailsLoading && (
            <p className="text-sm text-slate-500">Loading incident details...</p>
          )}

          {!detailsLoading && !selectedIncident && (
            <p className="text-sm text-slate-500">Select an incident to inspect evidence.</p>
          )}

          {!detailsLoading && selectedIncident && selectedDetails && (
            <div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-slate-950 px-3 py-1 text-xs font-semibold capitalize text-white">
                      {selectedIncident.severity}
                    </span>
                    <span className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold capitalize text-slate-700">
                      {selectedIncident.status}
                    </span>
                    <span className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-700">
                      Risk {selectedIncident.risk_score}
                    </span>
                    <span className="rounded-full border border-slate-300 px-3 py-1 text-xs font-semibold uppercase text-slate-700">
                      {selectedIncident.priority}
                    </span>
                  </div>

                  <h3 className="mt-3 text-xl font-semibold text-slate-950">
                    {selectedIncident.title}
                  </h3>
                </div>

                <button
                  type="button"
                  onClick={handleSummarize}
                  disabled={summaryLoading}
                  className="h-10 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:border-slate-500 disabled:cursor-not-allowed disabled:text-slate-400"
                >
                  {summaryLoading ? 'Refreshing...' : 'Refresh summary'}
                </button>
              </div>

              <p className="mt-3 text-sm leading-6 text-slate-700">
                {selectedIncident.ai_summary || selectedIncident.summary}
              </p>

              {selectedIncident.impact && (
                <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-900">
                  {selectedIncident.impact}
                </p>
              )}

              <div className="mt-5 grid gap-3 sm:grid-cols-3 xl:grid-cols-5">
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs font-medium text-slate-500">Created</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">
                    {formatTime(selectedIncident.created_at)}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs font-medium text-slate-500">Service</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">
                    {selectedIncident.service_name || 'Unmapped'}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs font-medium text-slate-500">Environment</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">
                    {selectedIncident.environment || 'Unknown'}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs font-medium text-slate-500">Evidence</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">
                    {selectedDetails.events.length} linked events
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 bg-white p-3">
                  <p className="text-xs font-medium text-slate-500">Graph</p>
                  <p className="mt-1 text-sm font-semibold text-slate-950">
                    {selectedDetails.graph.nodes.length} nodes / {selectedDetails.graph.edges.length} edges
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
                <div>
                  <h4 className="text-sm font-semibold text-slate-950">
                    Correlation graph
                  </h4>
                  <div className="mt-3 space-y-2">
                    {selectedDetails.graph.nodes.slice(0, 8).map((node) => (
                      <div
                        key={node.id}
                        className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3"
                      >
                        <span className="truncate text-sm font-medium text-slate-800">
                          {node.label}
                        </span>
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold capitalize text-slate-600">
                          {node.type}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-slate-950">
                    Evidence timeline
                  </h4>
                  <div className="mt-3 space-y-2">
                    {selectedDetails.events.map((event) => (
                      <div
                        key={`${event.id}-${event.timestamp}`}
                        className="rounded-lg border border-slate-200 bg-white p-3"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-sm font-semibold capitalize text-slate-950">
                            {event.source || 'unknown'}
                          </span>
                          <span className="text-xs text-slate-500">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>
                        <p className="mt-1 text-sm leading-5 text-slate-600">
                          {event.summary || [event.actor, event.action, event.target].filter(Boolean).join(' / ')}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {selectedDetails.history.length > 0 && (
                <div className="mt-5">
                  <h4 className="text-sm font-semibold text-slate-950">
                    Lifecycle
                  </h4>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {selectedDetails.history.slice(0, 4).map((item) => (
                      <div
                        key={item.id}
                        className="rounded-lg border border-slate-200 bg-white p-3"
                      >
                        <p className="text-sm font-semibold capitalize text-slate-950">
                          {item.from_status || 'new'} to {item.to_status}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {item.reason || 'Status changed'} / {formatTime(item.created_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        )}
      </div>
    </section>
  )
}
