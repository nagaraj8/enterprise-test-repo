export interface Incident {
  id: number
  title: string
  summary: string
  severity: string
  status: string
  priority: string
  service_name?: string | null
  owner?: string | null
  environment?: string | null
  impact?: string | null
  correlation_key?: string | null
  ai_summary?: string | null
  risk_score: number
  event_count: number
  detected_at?: string | null
  acknowledged_at?: string | null
  resolved_at?: string | null
  last_seen_at?: string | null
  created_at: string
  updated_at?: string | null
}

export interface IncidentEvent {
  id?: number | string
  source: string
  actor?: string | null
  action?: string | null
  target?: string | null
  event_type?: string | null
  service_name?: string | null
  environment?: string | null
  severity?: string | null
  fingerprint?: string | null
  timestamp?: string | null
  ingested_at?: string | null
  summary?: string | null
}

export interface CorrelationNode {
  id: string
  label: string
  type: 'incident' | 'event' | 'source'
  severity?: string
  source?: string
  timestamp?: string | null
}

export interface CorrelationEdge {
  from: string
  to: string
  label: string
}

export interface CorrelationGraph {
  nodes: CorrelationNode[]
  edges: CorrelationEdge[]
}

export interface IncidentDetails {
  incident: Incident
  events: IncidentEvent[]
  history: Array<{
    id: number
    incident_id: number
    from_status?: string | null
    to_status: string
    actor?: string | null
    reason?: string | null
    created_at: string
  }>
  notes: Array<{
    id: number
    incident_id: number
    note: string
    author?: string | null
    note_type: string
    created_at: string
  }>
  graph: CorrelationGraph
}

export interface DeploymentRisk {
  score: number
  level: string
  evaluated_at: string
  target?: string | null
  deployment_events: number
  factors: Array<{
    label: string
    count: number
  }>
  recommendations: string[]
  evidence: Array<IncidentEvent & {
    risk_score: number
    risk_factors: string[]
  }>
}
