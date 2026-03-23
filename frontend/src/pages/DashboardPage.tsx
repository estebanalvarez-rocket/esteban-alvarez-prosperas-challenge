import { useState } from "react"

import { JobForm } from "../components/JobForm"
import { REPORT_SCENARIOS } from "../constants/reportScenarios"
import { JobsTable } from "../components/JobsTable"
import { useAuth } from "../hooks/useAuth"
import { useJobsRealtime } from "../hooks/useJobsRealtime"
import { apiRequest } from "../services/api"

export function DashboardPage() {
  const { token, logout } = useAuth()
  const [reportType, setReportType] = useState(REPORT_SCENARIOS[0].value)
  const [dateFrom, setDateFrom] = useState("2026-03-01")
  const [dateTo, setDateTo] = useState("2026-03-22")
  const [format, setFormat] = useState("json")
  const [jobError, setJobError] = useState<string | null>(null)
  const [jobLoading, setJobLoading] = useState(false)

  const { jobs, loading: jobsLoading, error: jobsError, connected } = useJobsRealtime(token)

  const processingJobs = jobs.filter((job) => job.status === "PROCESSING").length
  const completedJobs = jobs.filter((job) => job.status === "COMPLETED").length
  const failedJobs = jobs.filter((job) => job.status === "FAILED").length

  const handleCreateJob = async () => {
    if (!token) {
      setJobError("Debes iniciar sesion antes de crear jobs")
      return
    }

    try {
      setJobLoading(true)
      setJobError(null)
      await apiRequest(
        "/jobs",
        "POST",
        {
          report_type: reportType,
          date_from: dateFrom,
          date_to: dateTo,
          format,
        },
        token,
      )
    } catch (error) {
      setJobError(error instanceof Error ? error.message : "No fue posible crear el job")
    } finally {
      setJobLoading(false)
    }
  }

  return (
    <main className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-block">
          <p className="eyebrow">Reports Console</p>
          <h2>Panel operativo</h2>
          <p>Desde aqui creas reportes, monitoreas estados y revisas resultados sin mezclar autenticacion con operacion.</p>
        </div>

        <div className="sidebar-block">
          <p className="mini-label">Vistas</p>
          <div className="sidebar-link active">Generador</div>
          <div className="sidebar-link active">Data table</div>
        </div>

        <button className="secondary-button sidebar-logout" onClick={logout} type="button">
          Cerrar sesion
        </button>
      </aside>

      <section className="dashboard-content">
        <section className="dashboard-grid">
          <JobForm
            reportType={reportType}
            dateFrom={dateFrom}
            dateTo={dateTo}
            format={format}
            loading={jobLoading}
            error={jobError}
            onReportTypeChange={setReportType}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            onFormatChange={setFormat}
            onSubmit={handleCreateJob}
          />

          <section className="panel status-panel">
            <div className="panel-header">
              <p className="eyebrow">Resumen</p>
              <h2>Actividad reciente</h2>
            </div>

            <div className="stats-showcase">
              <article className="stats-hero">
                <p className="stats-kicker">Jobs visibles</p>
                <span>{jobs.length}</span>
                <p className="stats-copy">Estado consolidado de los reportes cargados para este usuario.</p>
              </article>

              <div className="stats-grid">
                <article className="stat-tile processing">
                  <p className="stat-label">En proceso</p>
                  <span>{processingJobs}</span>
                  <p className="stat-footnote">Jobs tomados por el worker</p>
                </article>

                <article className="stat-tile completed">
                  <p className="stat-label">Completados</p>
                  <span>{completedJobs}</span>
                  <p className="stat-footnote">Resultados listos para descarga</p>
                </article>

                <article className="stat-tile failed">
                  <p className="stat-label">Fallidos</p>
                  <span>{failedJobs}</span>
                  <p className="stat-footnote">Requieren revision o reintento</p>
                </article>
              </div>
            </div>

            <div className={`feedback ${connected ? "info" : "error"}`}>
              {connected ? "Canal en tiempo real conectado" : "Canal en tiempo real desconectado"}
            </div>
            {jobsError ? <div className="feedback error">{jobsError}</div> : null}
          </section>
        </section>

        <JobsTable jobs={jobs} loading={jobsLoading} />
      </section>
    </main>
  )
}
