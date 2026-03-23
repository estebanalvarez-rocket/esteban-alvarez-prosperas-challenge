import { getReportScenario, REPORT_SCENARIOS } from "../constants/reportScenarios"

interface JobFormProps {
  reportType: string
  dateFrom: string
  dateTo: string
  format: string
  loading: boolean
  error: string | null
  onReportTypeChange: (value: string) => void
  onDateFromChange: (value: string) => void
  onDateToChange: (value: string) => void
  onFormatChange: (value: string) => void
  onSubmit: () => void
}

export function JobForm(props: JobFormProps) {
  const {
    reportType,
    dateFrom,
    dateTo,
    format,
    loading,
    error,
    onReportTypeChange,
    onDateFromChange,
    onDateToChange,
    onFormatChange,
    onSubmit,
  } = props

  const selectedScenario = getReportScenario(reportType) ?? REPORT_SCENARIOS[0]

  return (
    <section className="panel">
      <div className="panel-header">
        <p className="eyebrow">Nuevo job</p>
        <h2>Solicita un reporte asincrono</h2>
        <p className="section-copy">
          Cada tipo de reporte simula datos dummy, tiempos entre 5 y 30 segundos y distintos desenlaces: exito, retry o fallo final.
        </p>
      </div>

      <div className="simulation-card">
        <div>
          <p className="simulation-label">{selectedScenario.label}</p>
          <p className="simulation-copy">{selectedScenario.description}</p>
        </div>
        <div className="simulation-meta">
          <span className={`priority-chip ${selectedScenario.priority.toLowerCase()}`}>{selectedScenario.priority}</span>
          <span className="hint-pill">{selectedScenario.eta}</span>
          <span className="simulation-outcome">{selectedScenario.outcome}</span>
        </div>
      </div>

      <div className="grid">
        <label>
          Tipo de reporte
          <select value={reportType} onChange={(event) => onReportTypeChange(event.target.value)}>
            {REPORT_SCENARIOS.map((scenario) => (
              <option key={scenario.value} value={scenario.value}>
                {scenario.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Formato
          <select value={format} onChange={(event) => onFormatChange(event.target.value)}>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </select>
        </label>

        <label>
          Fecha desde
          <input type="date" value={dateFrom} onChange={(event) => onDateFromChange(event.target.value)} />
        </label>

        <label>
          Fecha hasta
          <input type="date" value={dateTo} onChange={(event) => onDateToChange(event.target.value)} />
        </label>
      </div>

      {error ? <div className="feedback error">{error}</div> : null}

      <div className="form-actions">
        <div className="hint-pill">Escenarios de demo activos</div>
        <button className="primary-button" disabled={loading} onClick={onSubmit} type="button">
          {loading ? "Creando..." : "Crear job"}
        </button>
      </div>
    </section>
  )
}
