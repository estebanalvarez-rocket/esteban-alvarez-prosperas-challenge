import type { Job } from "../hooks/useJobsRealtime"

interface JobsTableProps {
  jobs: Job[]
  loading: boolean
}

export function JobsTable({ jobs, loading }: JobsTableProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <p className="eyebrow">Estado en vivo</p>
        <h2>Ultimos jobs</h2>
      </div>

      {loading ? <div className="feedback info">Actualizando lista...</div> : null}

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Rango</th>
              <th>Formato</th>
              <th>Estado</th>
              <th>Prioridad</th>
              <th>Intentos</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  Todavia no hay jobs para este usuario.
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.job_id}>
                  <td data-label="Tipo">{job.report_type}</td>
                  <td data-label="Rango">{job.date_from} a {job.date_to}</td>
                  <td data-label="Formato">{job.report_format.toUpperCase()}</td>
                  <td data-label="Estado">
                    <span className={`badge ${job.status.toLowerCase()}`}>{job.status}</span>
                  </td>
                  <td data-label="Prioridad">
                    <span className={`priority-chip ${job.priority.toLowerCase()}`}>{job.priority}</span>
                  </td>
                  <td data-label="Intentos">{job.attempt_count}</td>
                  <td data-label="Resultado">
                    {job.result_url ? (
                      <a href={job.result_url} target="_blank" rel="noreferrer">
                        Ver archivo
                      </a>
                    ) : job.error_message ? (
                      <span className="inline-error">{job.error_message}</span>
                    ) : job.next_retry_at ? (
                      <span>Retry: {new Date(job.next_retry_at).toLocaleTimeString()}</span>
                    ) : (
                      "Pendiente"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
