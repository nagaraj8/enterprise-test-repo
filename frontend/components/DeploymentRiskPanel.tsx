"use client"

import { useEffect, useState } from 'react'
import { fetchDeploymentRisk } from '../services/incident'
import { DeploymentRisk } from '../types/incident'

const levelStyles: Record<string, string> = {
  critical: 'bg-rose-600 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-amber-400 text-slate-950',
  low: 'bg-emerald-500 text-white',
}

function formatTime(timestamp?: string | null) {
  if (!timestamp) return 'Unknown'

  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) return timestamp

  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default function DeploymentRiskPanel() {
  const [risk, setRisk] = useState<DeploymentRisk | null>(null)
  const [target, setTarget] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadRisk(nextTarget = target) {
    try {
      setLoading(true)
      setError('')
      const data = await fetchDeploymentRisk(nextTarget.trim() || undefined)

      setRisk(data)
    } catch (error) {
      console.error(error)
      setError('Deployment risk unavailable.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      async function loadInitialRisk() {
        try {
          setLoading(true)
          setError('')
          const data = await fetchDeploymentRisk()

          setRisk(data)
        } catch (error) {
          console.error(error)
          setError('Deployment risk unavailable.')
        } finally {
          setLoading(false)
        }
      }

      loadInitialRisk()
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [])

  const level = risk?.level?.toLowerCase() ?? 'medium'

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase text-slate-500">
            Deployment risk
          </p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-950">
            Release readiness
          </h2>
        </div>

        {risk && (
          <div className={`rounded-lg px-4 py-3 text-center ${levelStyles[level] ?? levelStyles.medium}`}>
            <p className="text-xs font-semibold uppercase">Risk</p>
            <p className="text-2xl font-semibold">{risk.score}</p>
          </div>
        )}
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={target}
          onChange={(event) => setTarget(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              loadRisk()
            }
          }}
          placeholder="Service or repository"
          className="h-11 flex-1 rounded-lg border border-slate-300 bg-slate-50 px-3 text-sm outline-none transition focus:border-slate-900 focus:bg-white"
        />
        <button
          type="button"
          onClick={() => loadRisk()}
          disabled={loading}
          className="h-11 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? 'Checking...' : 'Assess'}
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      {risk && (
        <div className="mt-5 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="space-y-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">Level</p>
              <p className="mt-1 text-lg font-semibold capitalize text-slate-950">
                {risk.level}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {risk.deployment_events} deployment signals / {formatTime(risk.evaluated_at)}
              </p>
            </div>

            {risk.factors.map((factor) => (
              <div
                key={factor.label}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3"
              >
                <span className="text-sm font-medium text-slate-700">
                  {factor.label}
                </span>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                  {factor.count}
                </span>
              </div>
            ))}
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-950">
              Evidence
            </h3>
            <div className="mt-3 space-y-3">
              {risk.evidence.length === 0 && (
                <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
                  No deployment evidence matched.
                </div>
              )}

              {risk.evidence.map((event, index) => (
                <div
                  key={`${event.id ?? index}-${event.timestamp ?? index}`}
                  className="rounded-lg border border-slate-200 p-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-semibold capitalize text-slate-950">
                      {event.source || 'unknown'}
                    </span>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                      {event.risk_score}
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
      )}
    </section>
  )
}
