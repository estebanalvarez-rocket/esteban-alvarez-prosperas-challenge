import random
import time
from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


class SimulationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReportSimulationProfile:
    report_type: str
    label: str
    description: str
    outcome: str
    min_seconds: int
    max_seconds: int


REPORT_SIMULATION_PROFILES = {
    "sales_summary": ReportSimulationProfile(
        report_type="sales_summary",
        label="Sales summary",
        description="Siempre completa con metricas comerciales dummy.",
        outcome="success",
        min_seconds=5,
        max_seconds=12,
    ),
    "customer_ltv": ReportSimulationProfile(
        report_type="customer_ltv",
        label="Customer LTV",
        description="Completa con cohortes y lifetime value simulados.",
        outcome="success",
        min_seconds=8,
        max_seconds=18,
    ),
    "fraud_alert": ReportSimulationProfile(
        report_type="fraud_alert",
        label="Fraud alert",
        description="Falla una vez y luego reintenta hasta completar.",
        outcome="retry_once",
        min_seconds=5,
        max_seconds=10,
    ),
    "security_incident": ReportSimulationProfile(
        report_type="security_incident",
        label="Security incident",
        description="Escenario de error persistente para mostrar fallos finales.",
        outcome="always_fail",
        min_seconds=6,
        max_seconds=9,
    ),
    "inventory_snapshot": ReportSimulationProfile(
        report_type="inventory_snapshot",
        label="Inventory snapshot",
        description="Completa con inventario y rotacion simulados.",
        outcome="success",
        min_seconds=7,
        max_seconds=16,
    ),
    "ops_resilience": ReportSimulationProfile(
        report_type="ops_resilience",
        label="Ops resilience",
        description="Escenario mixto con posibilidad de retry o exito directo.",
        outcome="flaky",
        min_seconds=10,
        max_seconds=30,
    ),
}


def get_report_simulation_profile(report_type: str) -> ReportSimulationProfile:
    return REPORT_SIMULATION_PROFILES.get(
        report_type,
        ReportSimulationProfile(
            report_type=report_type,
            label=report_type.replace("_", " ").title(),
            description="Escenario generico con resultado exitoso.",
            outcome="success",
            min_seconds=5,
            max_seconds=15,
        ),
    )


def get_simulated_delay_seconds(report_type: str) -> int:
    profile = get_report_simulation_profile(report_type)
    min_seconds = max(settings.worker_sleep_min_seconds, profile.min_seconds)
    max_seconds = min(settings.worker_sleep_max_seconds, profile.max_seconds)
    if min_seconds > max_seconds:
        max_seconds = min_seconds
    return random.randint(min_seconds, max_seconds)


def maybe_raise_simulation_error(report_type: str, receive_count: int) -> None:
    profile = get_report_simulation_profile(report_type)
    if profile.outcome == "retry_once" and receive_count == 1:
        raise SimulationError("Simulated transient upstream timeout. Retry expected.")
    if profile.outcome == "always_fail":
        raise SimulationError("Simulated persistent processing failure for this report type.")
    if profile.outcome == "flaky":
        if receive_count == 1 and random.random() < 0.45:
            raise SimulationError("Simulated intermittent downstream dependency error.")
        if receive_count >= 2 and random.random() < 0.15:
            raise SimulationError("Simulated repeated flaky processing error.")


def build_dummy_rows(report_type: str) -> list[dict]:
    profile = get_report_simulation_profile(report_type)
    if profile.report_type == "sales_summary":
        return [
            {"metric": "gross_revenue", "value": round(random.uniform(12000, 34000), 2)},
            {"metric": "orders", "value": random.randint(180, 420)},
            {"metric": "avg_ticket", "value": round(random.uniform(55, 140), 2)},
        ]
    if profile.report_type == "customer_ltv":
        return [
            {"segment": "new_users", "ltv": round(random.uniform(180, 260), 2)},
            {"segment": "repeat_buyers", "ltv": round(random.uniform(320, 540), 2)},
            {"segment": "vip", "ltv": round(random.uniform(650, 1200), 2)},
        ]
    if profile.report_type == "fraud_alert":
        return [
            {"risk_level": "critical", "events": random.randint(2, 9)},
            {"risk_level": "medium", "events": random.randint(10, 28)},
            {"risk_level": "low", "events": random.randint(30, 75)},
        ]
    if profile.report_type == "security_incident":
        return [
            {"system": "edge_api", "incidents": random.randint(1, 4)},
            {"system": "auth_service", "incidents": random.randint(1, 3)},
            {"system": "admin_console", "incidents": random.randint(0, 2)},
        ]
    if profile.report_type == "inventory_snapshot":
        return [
            {"warehouse": "bogota", "stock_units": random.randint(1200, 4300)},
            {"warehouse": "medellin", "stock_units": random.randint(800, 2600)},
            {"warehouse": "cali", "stock_units": random.randint(600, 2100)},
        ]
    if profile.report_type == "ops_resilience":
        return [
            {"queue_depth": random.randint(2, 20)},
            {"retry_jobs": random.randint(0, 6)},
            {"completed_last_hour": random.randint(12, 48)},
        ]
    return [
        {"metric": "active_users", "value": random.randint(100, 500)},
        {"metric": "revenue", "value": round(random.uniform(1000, 5000), 2)},
    ]


def simulate_report_processing(report_type: str, receive_count: int) -> dict:
    sleep_seconds = get_simulated_delay_seconds(report_type)
    time.sleep(sleep_seconds)
    maybe_raise_simulation_error(report_type, receive_count)
    profile = get_report_simulation_profile(report_type)
    return {
        "profile": profile.report_type,
        "label": profile.label,
        "description": profile.description,
        "simulated_processing_seconds": sleep_seconds,
        "receive_count": receive_count,
        "rows": build_dummy_rows(report_type),
    }
