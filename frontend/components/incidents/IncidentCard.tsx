import { Incident } from "../../types/incident"

interface Props {
  incident: Incident
  active?: boolean
  onSelect?: (incident: Incident) => void
}

const severityStyles: Record<string, string> = {
  critical: 'border-rose-500 bg-rose-50 text-rose-800',
  high: 'border-orange-300 bg-orange-50 text-orange-800',
  medium: 'border-amber-300 bg-amber-50 text-amber-800',
  low: 'border-emerald-300 bg-emerald-50 text-emerald-800',
}

function formatTime(timestamp?: string | null) {
  if (!timestamp) return 'No timestamp'

  const date = new Date(timestamp)

  if (Number.isNaN(date.getTime())) return timestamp

  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export default function IncidentCard({
  incident,
  active = false,
  onSelect,
}: Props) {
  const severityClass =
    severityStyles[incident.severity?.toLowerCase()] ?? severityStyles.medium

  return (
    <button
      type="button"
      onClick={() => onSelect?.(incident)}
      className={`w-full rounded-lg border p-4 text-left transition ${
        active
          ? 'border-slate-950 bg-slate-50 shadow-sm'
          : 'border-slate-200 bg-white hover:border-slate-400'
      }`}
    >

      <div className="flex items-start justify-between gap-3">

        <h3 className="min-w-0 text-sm font-semibold leading-5 text-slate-950">
          {incident.title}
        </h3>

        <span className={`shrink-0 rounded-full border px-2 py-1 text-xs font-semibold capitalize ${severityClass}`}>
          {incident.severity}
        </span>
      </div>

      <p className="mt-2 line-clamp-2 text-sm leading-5 text-slate-600">
        {incident.summary}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span>{formatTime(incident.created_at)}</span>
        <span>/</span>
        <span>{incident.service_name || 'Unmapped service'}</span>
        <span>/</span>
        <span className="uppercase">{incident.priority || 'p3'}</span>
        <span>/</span>
        <span>{incident.event_count || 0} events</span>
        <span>/</span>
        <span>Risk {incident.risk_score ?? 50}</span>
      </div>
    </button>
  )
}
