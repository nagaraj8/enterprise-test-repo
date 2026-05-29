import { request } from './client'
import {
  DeploymentRisk,
  Incident,
  IncidentDetails,
} from '../types/incident'

export async function fetchIncidents() {
  return request<{ incidents: Incident[] }>('/incidents')
}

export async function runCorrelation() {
  return request<{ incidents_created: Array<{ incident_id: number }> }>(
    '/incidents/correlate',
    {
      method: 'POST',
    }
  )
}

export async function fetchIncidentDetails(incidentId: number) {
  return request<IncidentDetails>(`/incidents/${incidentId}`)
}

export async function summarizeIncident(incidentId: number) {
  return request<{ ai_summary: string; risk_score: number }>(
    `/incidents/${incidentId}/summarize`,
    {
      method: 'POST',
    }
  )
}

export async function fetchDeploymentRisk(target?: string) {
  const query = target ? `?target=${encodeURIComponent(target)}` : ''

  return request<DeploymentRisk>(`/deployments/risk${query}`)
}
