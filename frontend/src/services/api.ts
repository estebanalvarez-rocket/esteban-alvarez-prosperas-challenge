const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const defaultApiBaseUrl = import.meta.env.PROD ? window.location.origin : "http://localhost:8000"

export const API_BASE_URL = configuredApiBaseUrl || defaultApiBaseUrl

type HttpMethod = "GET" | "POST"

export async function apiRequest<T>(
  path: string,
  method: HttpMethod,
  body?: unknown,
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unexpected request error" }))
    throw new Error(error.detail ?? "Unexpected request error")
  }

  return response.json() as Promise<T>
}
