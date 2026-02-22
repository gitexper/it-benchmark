"""
Analysis engine — computes derived metrics, quartile positioning, and normalized scores.
"""
from data.benchmarks import get_benchmarks, METRIC_ORDER


def compute_derived_metrics(client_data: dict) -> dict:
    """
    Takes raw client inputs and computes all benchmark-comparable metrics.
    Returns a dict keyed by metric_id -> computed value.
    """
    results = {}
    revenue = client_data.get("revenue", 0)
    total_employees = client_data.get("total_employees", 0)
    it_budget = client_data.get("it_budget", 0)
    it_budget_prior = client_data.get("it_budget_prior_year", 0)
    it_ftes = client_data.get("it_ftes", 0)
    total_opex = client_data.get("total_opex", 0)

    # Spend metrics
    if revenue > 0:
        results["it_spend_pct_revenue"] = (it_budget / revenue) * 100

    if total_employees > 0:
        results["it_spend_per_employee"] = it_budget / total_employees

    if total_opex > 0:
        results["it_spend_pct_opex"] = (it_budget / total_opex) * 100

    if it_budget_prior > 0:
        results["it_budget_yoy_growth"] = (
            (it_budget - it_budget_prior) / it_budget_prior
        ) * 100

    # Staffing metrics
    if total_employees > 0:
        results["it_staff_pct_employees"] = (it_ftes / total_employees) * 100

    if it_ftes > 0:
        results["it_staffing_ratio"] = total_employees / it_ftes

    # Budget allocation (Run / Grow / Transform)
    results["run_budget_pct"] = client_data.get("run_pct", None)
    results["grow_budget_pct"] = client_data.get("grow_pct", None)
    results["transform_budget_pct"] = client_data.get("transform_pct", None)

    # Technology mix
    if it_budget > 0:
        cloud_spend = client_data.get("cloud_spend", 0)
        results["cloud_pct_budget"] = (cloud_spend / it_budget) * 100

        cyber_spend = client_data.get("cybersecurity_spend", 0)
        results["cybersecurity_pct_budget"] = (cyber_spend / it_budget) * 100

    # Cost structure
    if it_budget > 0:
        labor_cost = client_data.get("it_labor_cost", 0)
        results["it_labor_pct_budget"] = (labor_cost / it_budget) * 100

        outsourcing_spend = client_data.get("outsourcing_spend", 0)
        results["outsourcing_pct_budget"] = (outsourcing_spend / it_budget) * 100

        app_spend = client_data.get("application_spend", 0)
        infra_spend = client_data.get("infrastructure_spend", 0)
        total_app_infra = app_spend + infra_spend
        if total_app_infra > 0:
            results["app_pct_budget"] = (app_spend / total_app_infra) * 100

    # Operational metrics (direct inputs)
    results["system_availability"] = client_data.get("system_availability", None)
    results["it_attrition_rate"] = client_data.get("it_attrition_rate", None)
    results["helpdesk_cost_per_ticket"] = client_data.get(
        "helpdesk_cost_per_ticket", None
    )

    # Strip None values
    return {k: v for k, v in results.items() if v is not None}


def get_quartile_position(bench: dict, value: float) -> str:
    """
    Determine which quartile the client falls in for a given metric.
    Returns one of: 'top_quartile', 'above_median', 'below_median', 'bottom_quartile'
    """
    tq = bench["top_quartile"]
    med = bench["median"]
    bq = bench["bottom_quartile"]
    direction = bench["direction"]

    if direction == "lower_is_better":
        if value <= tq:
            return "top_quartile"
        elif value <= med:
            return "above_median"
        elif value <= bq:
            return "below_median"
        else:
            return "bottom_quartile"
    else:
        if value >= tq:
            return "top_quartile"
        elif value >= med:
            return "above_median"
        elif value >= bq:
            return "below_median"
        else:
            return "bottom_quartile"


def normalize_score(bench: dict, value: float) -> float:
    """
    Normalize a metric value to a 0-100 scale where:
    - 100 = at or beyond top quartile (best)
    - 50 = at median
    - 0 = at or beyond bottom quartile (worst)
    """
    tq = bench["top_quartile"]
    med = bench["median"]
    bq = bench["bottom_quartile"]
    direction = bench["direction"]

    if direction == "lower_is_better":
        if value <= tq:
            return 100.0
        elif value >= bq:
            return 0.0
        elif value <= med:
            range_val = med - tq
            if range_val == 0:
                return 75.0
            return 50.0 + 50.0 * (med - value) / range_val
        else:
            range_val = bq - med
            if range_val == 0:
                return 25.0
            return 50.0 * (bq - value) / range_val
    else:
        if value >= tq:
            return 100.0
        elif value <= bq:
            return 0.0
        elif value >= med:
            range_val = tq - med
            if range_val == 0:
                return 75.0
            return 50.0 + 50.0 * (value - med) / range_val
        else:
            range_val = med - bq
            if range_val == 0:
                return 25.0
            return 50.0 * (value - bq) / range_val


def get_insight(bench: dict, quartile: str) -> str:
    """Return contextual insight text based on quartile position."""
    if quartile in ("top_quartile", "above_median"):
        direction = bench["direction"]
        if direction == "lower_is_better":
            return bench["insight_low"]
        else:
            return bench["insight_high"]
    elif quartile in ("bottom_quartile", "below_median"):
        direction = bench["direction"]
        if direction == "lower_is_better":
            return bench["insight_high"]
        else:
            return bench["insight_low"]
    return bench["insight_aligned"]


def get_delta_vs_median(bench: dict, value: float) -> dict:
    """Calculate the delta between client value and median."""
    med = bench["median"]
    delta = value - med
    if med != 0:
        delta_pct = (delta / med) * 100
    else:
        delta_pct = 0
    return {"delta": delta, "delta_pct": delta_pct}


def run_full_analysis(client_data: dict, industry: str = "financial_services") -> list[dict]:
    """
    Run the complete analysis pipeline. Returns a list of result dicts,
    one per metric, in display order.
    """
    benchmarks = get_benchmarks(industry)
    derived = compute_derived_metrics(client_data)
    results = []

    for metric_id in METRIC_ORDER:
        if metric_id not in derived or metric_id not in benchmarks:
            continue

        bench = benchmarks[metric_id]
        value = derived[metric_id]
        quartile = get_quartile_position(bench, value)
        score = normalize_score(bench, value)
        delta = get_delta_vs_median(bench, value)
        insight = get_insight(bench, quartile)

        results.append(
            {
                "metric_id": metric_id,
                "name": bench["name"],
                "category": bench["category"],
                "unit": bench["unit"],
                "format": bench["format"],
                "value": value,
                "top_quartile": bench["top_quartile"],
                "median": bench["median"],
                "bottom_quartile": bench["bottom_quartile"],
                "direction": bench["direction"],
                "quartile": quartile,
                "score": score,
                "delta": delta["delta"],
                "delta_pct": delta["delta_pct"],
                "insight": insight,
                "source": bench["source"],
            }
        )

    return results


def get_summary_stats(results: list[dict]) -> dict:
    """Compute summary statistics across all analyzed metrics."""
    total = len(results)
    if total == 0:
        return {"total": 0, "top_q": 0, "above_med": 0, "below_med": 0, "bottom_q": 0, "avg_score": 0}

    top_q = sum(1 for r in results if r["quartile"] == "top_quartile")
    above_med = sum(1 for r in results if r["quartile"] == "above_median")
    below_med = sum(1 for r in results if r["quartile"] == "below_median")
    bottom_q = sum(1 for r in results if r["quartile"] == "bottom_quartile")
    avg_score = sum(r["score"] for r in results) / total

    return {
        "total": total,
        "top_q": top_q,
        "above_med": above_med,
        "below_med": below_med,
        "bottom_q": bottom_q,
        "avg_score": avg_score,
    }
