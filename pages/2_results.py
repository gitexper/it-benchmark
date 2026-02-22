"""
Page 2: Results Dashboard — Summary scorecard, radar chart, bar charts, table.
"""
import streamlit as st
import pandas as pd
from analysis.engine import run_full_analysis, get_summary_stats
from charts.plots import (
    create_radar_chart,
    create_summary_gauge,
    create_category_bar_chart,
    COLORS,
    QUARTILE_LABELS,
)


def format_value(value, unit, fmt):
    """Format a metric value for display."""
    if unit == "$":
        return f"${value:{fmt}}"
    elif unit == "%":
        return f"{value:{fmt}}%"
    elif unit == "ratio":
        return f"1:{value:.0f}"
    else:
        return f"{value:{fmt}}"


def show():
    st.header("Benchmark Results Dashboard")

    if not st.session_state.get("analysis_run"):
        st.info("Enter client data on the **Client Input** page first, then return here.")
        return

    client_data = st.session_state["client_data"]
    company_name = client_data.get("company_name", "Client")
    industry = client_data.get("industry", "financial_services")
    industry_name = client_data.get("industry_name", "Financial Services")

    # Run analysis with selected industry
    results = run_full_analysis(client_data, industry=industry)
    st.session_state["analysis_results"] = results

    if not results:
        st.warning("No metrics could be computed. Please check the input data.")
        return

    summary = get_summary_stats(results)

    # ── Header ─────────────────────────────────────────────────────
    st.subheader(f"Benchmarking Report: {company_name}")
    st.caption(f"Industry: {industry_name} — {client_data.get('sub_vertical', 'N/A')}")

    # ── Summary Scorecard ──────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Metrics Analyzed", summary["total"])
    col2.metric("Top Quartile", summary["top_q"], help="Metrics where you outperform 75% of peers")
    col3.metric("Above Median", summary["above_med"], help="Metrics better than average")
    col4.metric("Below Median", summary["below_med"], help="Metrics below average")
    col5.metric("Bottom Quartile", summary["bottom_q"], help="Metrics where 75% of peers outperform you")

    st.divider()

    # ── Gauge + Radar side by side ─────────────────────────────────
    col_left, col_right = st.columns([1, 2])

    with col_left:
        gauge = create_summary_gauge(summary["avg_score"])
        st.plotly_chart(gauge, use_container_width=True)

        # Quick interpretation
        score = summary["avg_score"]
        if score >= 75:
            st.success("**Strong overall positioning** — you outperform most peers.")
        elif score >= 50:
            st.info("**Solid positioning** — performing at or above the industry median.")
        elif score >= 25:
            st.warning("**Room for improvement** — several metrics trail the median.")
        else:
            st.error("**Significant gaps** — most metrics are below industry benchmarks.")

    with col_right:
        radar = create_radar_chart(results)
        st.plotly_chart(radar, use_container_width=True)

    st.divider()

    # ── All Metrics Bar Chart ──────────────────────────────────────
    bar_chart = create_category_bar_chart(results)
    st.plotly_chart(bar_chart, use_container_width=True)

    st.divider()

    # ── Detailed Table ─────────────────────────────────────────────
    st.subheader("Detailed Comparison Table")

    table_data = []
    for r in results:
        quartile_label = QUARTILE_LABELS[r["quartile"]]
        delta_pct = r["delta_pct"]
        delta_str = f"{delta_pct:+.1f}% vs median"

        table_data.append(
            {
                "Category": r["category"],
                "Metric": r["name"],
                "Your Value": format_value(r["value"], r["unit"], r["format"]),
                "Top Quartile": format_value(r["top_quartile"], r["unit"], r["format"]),
                "Median": format_value(r["median"], r["unit"], r["format"]),
                "Bottom Quartile": format_value(r["bottom_quartile"], r["unit"], r["format"]),
                "Position": quartile_label,
                "Delta": delta_str,
                "Score": f"{r['score']:.0f}/100",
            }
        )

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    # ── Key Findings ───────────────────────────────────────────────
    st.divider()
    st.subheader("Key Findings")

    # Strengths (top quartile)
    strengths = [r for r in results if r["quartile"] == "top_quartile"]
    weaknesses = [r for r in results if r["quartile"] == "bottom_quartile"]
    opportunities = [r for r in results if r["quartile"] == "below_median"]

    if strengths:
        st.markdown("**Strengths (Top Quartile)**")
        for r in strengths:
            st.markdown(f"- **{r['name']}**: {format_value(r['value'], r['unit'], r['format'])} — {r['insight']}")

    if weaknesses:
        st.markdown("**Areas of Concern (Bottom Quartile)**")
        for r in weaknesses:
            st.markdown(f"- **{r['name']}**: {format_value(r['value'], r['unit'], r['format'])} — {r['insight']}")

    if opportunities:
        st.markdown("**Improvement Opportunities (Below Median)**")
        for r in opportunities:
            st.markdown(f"- **{r['name']}**: {format_value(r['value'], r['unit'], r['format'])} — {r['insight']}")

    if not strengths and not weaknesses and not opportunities:
        st.markdown("All metrics are at or near the industry median. A solid, balanced position.")


show()
