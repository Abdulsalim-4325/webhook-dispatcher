/**
 * API client bindings for Sentinel Dispatcher backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface HealthStatus {
  status: string;
  database?: string;
  redis?: string;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health/ready`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function triggerTestEvent(eventType: string, payload: Record<string, unknown>, idempotencyKey: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/events/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify({
      event_type: eventType,
      idempotency_key: idempotencyKey,
      payload,
    }),
  });
  return response.json();
}
