export interface ReportScenario {
  value: string
  label: string
  priority: "HIGH" | "STANDARD"
  eta: string
  outcome: string
  description: string
}

export const REPORT_SCENARIOS: ReportScenario[] = [
  {
    value: "sales_summary",
    label: "Sales summary",
    priority: "STANDARD",
    eta: "5-12s",
    outcome: "Completado",
    description: "Reporte comercial estable con ventas, ordenes y ticket promedio dummy.",
  },
  {
    value: "customer_ltv",
    label: "Customer LTV",
    priority: "STANDARD",
    eta: "8-18s",
    outcome: "Completado",
    description: "Simula cohortes, segmentos y lifetime value de clientes.",
  },
  {
    value: "inventory_snapshot",
    label: "Inventory snapshot",
    priority: "STANDARD",
    eta: "7-16s",
    outcome: "Completado",
    description: "Genera stock, rotacion y capacidad por bodega.",
  },
  {
    value: "fraud_alert",
    label: "Fraud alert",
    priority: "HIGH",
    eta: "5-10s + retry",
    outcome: "Retry y luego completado",
    description: "La primera ejecucion falla a proposito y luego completa en el siguiente intento.",
  },
  {
    value: "security_incident",
    label: "Security incident",
    priority: "HIGH",
    eta: "6-9s",
    outcome: "Fallo final",
    description: "Escenario de error persistente para mostrar retries agotados y estado FAILED.",
  },
  {
    value: "ops_resilience",
    label: "Ops resilience",
    priority: "STANDARD",
    eta: "10-30s",
    outcome: "Mixto",
    description: "Escenario flaky con posibilidad de exito directo o retry intermitente.",
  },
]

export function getReportScenario(reportType: string): ReportScenario | undefined {
  return REPORT_SCENARIOS.find((scenario) => scenario.value === reportType)
}
