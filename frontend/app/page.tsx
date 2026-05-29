'use client'

import { useEffect, useMemo, useState } from 'react'
import AIQueryBox from '../components/AIQueryBox'
import Timeline from '../components/Timeline'
import SemanticSearch from '../components/SemanticSearch'
import IncidentPanel from "../components/incidents/IncidentPanel"
import DeploymentRiskPanel from '../components/DeploymentRiskPanel'
import { Overview } from '../services/client'
import { fetchOverview, fetchSources } from '../services/overview'

const sources = ['all', 'github', 'slack', 'incident', 'deploy']
type WorkspaceView = 'incidents' | 'timeline' | 'risk' | 'search' | 'ai'

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
  const [activeView, setActiveView] = useState<WorkspaceView>('incidents')
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
  const workspaceViews: Array<{
    id: WorkspaceView
    label: string
    value: string
    context: string
  }> = [
    {
      id: 'incidents',
      label: 'Active incidents',
      value: formatCount(overview?.open_incidents),
      context: 'open',
    },
    {
      id: 'timeline',
      label: 'Operational timeline',
      value: formatCount(overview?.events_last_24h),
      context: '24h',
    },
    {
      id: 'risk',
      label: 'Release readiness',
      value: formatCount(overview?.deployments_last_24h),
      context: 'deploys',
    },
    {
      id: 'search',
      label: 'Find related activity',
      value: formatCount(overview?.total_events),
      context: 'events',
    },
    {
      id: 'ai',
      label: 'Ask AI',
      value: 'AI',
      context: 'context',
    },
  ]

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
        <header className="grid gap-5 border-b border-slate-200 pb-5 lg:grid-cols-[0.7fr_1.3fr] lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase text-emerald-700">
              Enterprise AI operations
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-950 sm:text-4xl">
              Enterprise Decision Brain
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Incidents, timelines, release risk, related activity, and AI answers in one focused console.
            </p>
          </div>

          <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-6">
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
              <p className="text-xs font-medium text-slate-500">Open incidents</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatCount(overview?.open_incidents)}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium text-slate-500">Services</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatCount(overview?.services)}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium text-slate-500">Deploys 24h</p>
              <p className="mt-1 text-lg font-semibold text-slate-950">
                {formatCount(overview?.deployments_last_24h)}
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

        <section className="sticky top-0 z-20 rounded-lg border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur">
          <div className="grid gap-4 xl:grid-cols-[1fr_auto] xl:items-center">
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
              <p className="text-sm text-slate-500">
                Sources: {Math.max(availableSources.length - 1, 0)}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
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

          <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_auto] lg:items-end">
            <label className="block">
              <span className="text-sm font-semibold text-slate-700">
                Filter
              </span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Service, actor, action, target, or source"
                className="mt-2 h-11 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 text-sm outline-none transition focus:border-slate-900 focus:bg-white"
              />
            </label>

            <div>
              <p className="text-sm font-semibold text-slate-700">Workspace</p>
              <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                {workspaceViews.map((view) => (
                  <button
                    key={view.id}
                    type="button"
                    onClick={() => setActiveView(view.id)}
                    aria-pressed={activeView === view.id}
                    className={`min-h-16 rounded-lg border p-3 text-left transition ${
                      activeView === view.id
                        ? 'border-slate-950 bg-slate-950 text-white shadow-sm'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-400 hover:bg-white'
                    }`}
                  >
                    <span className="block text-sm font-semibold">
                      {view.label}
                    </span>
                    <span className={`mt-1 block text-xs ${activeView === view.id ? 'text-slate-300' : 'text-slate-500'}`}>
                      {view.value} {view.context}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {activeView === 'incidents' && <IncidentPanel />}
        {activeView === 'timeline' && <Timeline source={source} query={query} />}
        {activeView === 'risk' && <DeploymentRiskPanel />}
        {activeView === 'search' && <SemanticSearch source={source} />}
        {activeView === 'ai' && <AIQueryBox />}
      </div>
    </main>
  )
}
