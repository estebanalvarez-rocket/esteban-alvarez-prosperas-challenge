import { useEffect, useState } from "react"

import { API_BASE_URL, apiRequest } from "../services/api"

export interface Job {
  job_id: string
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  priority: "HIGH" | "STANDARD"
  report_type: string
  report_format: string
  date_from: string
  date_to: string
  created_at: string
  updated_at: string
  result_url: string | null
  error_message: string | null
  attempt_count: number
  next_retry_at: string | null
}

interface JobListResponse {
  items: Job[]
}

interface JobRealtimeMessage {
  type: string
  jobs: Job[]
}

const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws")

export function useJobsRealtime(token: string | null) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!token) {
      setJobs([])
      setConnected(false)
      return
    }

    let active = true
    let socket: WebSocket | null = null

    const loadInitialJobs = async () => {
      try {
        setLoading(true)
        const response = await apiRequest<JobListResponse>("/jobs?page=1&page_size=20", "GET", undefined, token)
        if (active) {
          setJobs(response.items)
          setError(null)
        }
      } catch (requestError) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : "No se pudo cargar jobs")
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadInitialJobs()

    socket = new WebSocket(`${WS_BASE_URL}/api/ws/jobs?token=${encodeURIComponent(token)}`)

    socket.onopen = () => {
      if (active) {
        setConnected(true)
        setError(null)
      }
    }

    socket.onmessage = (event) => {
      if (!active) {
        return
      }
      const payload = JSON.parse(event.data) as JobRealtimeMessage
      if (payload.type === "jobs.snapshot") {
        setJobs(payload.jobs)
      }
    }

    socket.onclose = () => {
      if (active) {
        setConnected(false)
      }
    }

    socket.onerror = () => {
      if (active) {
        setError("No se pudo conectar al canal en tiempo real")
      }
    }

    return () => {
      active = false
      socket?.close()
    }
  }, [token])

  return { jobs, loading, error, connected }
}
