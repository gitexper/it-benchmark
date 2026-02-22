"""
Page 3: Detailed Analysis — drill into each metric with context and insights.
"""
import streamlit as st
from analysis.engine import run_full_analysis
from charts.plots import create_metric_bar_chart, COLORS, QUARTILE_LABELS
from data.benchmarks import CATEGORIES, get_benchmarks


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
    st.header("Detailed Metric Analysis")

    if not st.session_state.get("analysis_run"):
        st.info("Enter client data on the **Client Input** page first, then return here.")
        return

    client_data = st.session_state["client_data"]
    company_name = client_data.get("company_name", "Client")
    industry = client_data.get("industry", "financial_services")
    industry_name = client_data.get("industry_name", "Financial Services")
    results = run_full_analysis(client_data, industry=industry)

    if not results:
        st.warning("No metrics could be computed. Please check the input data.")
        return

    st.caption(f"Detailed analysis for **{company_name}** — {industry_name} benchmarks")

    # Get benchmark data for description lookups
    benchmarks = get_benchmarks(industry)

    # Group results by category
    results_by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in results_by_category:
            results_by_category[cat] = []
        results_by_category[cat].append(r)

    # Category icons
    cat_icons = {
        "Spend": "Spend",
        "Staffing": "Staffing",
        "Budget Allocation": "Budget Allocation",
        "Technology Mix": "Technology Mix",
        "Cost Structure": "Cost Structure",
        "Operations": "Operations",
    }

    # Display by category
    for category in CATEGORIES:
        if category not in results_by_category:
            continue

        st.subheader(cat_icons.get(category, category))

        for r in results_by_category[category]:
            quartile = r["quartile"]
            quartile_label = QUARTILE_LABELS[quartile]
            color = COLORS[quartile]

            with st.expander(
                f"**{r['name']}** — {quartile_label}  |  Score: {r['score']:.0f}/100",
                expanded=(quartile in ("bottom_quartile",)),
            ):
                # Metric overview
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Your Value", format_value(r["value"], r["unit"], r["format"]))
                col2.metric("Industry Median", format_value(r["median"], r["unit"], r["format"]))
                col3.metric("Top Quartile", format_value(r["top_quartile"], r["unit"], r["format"]))
                col4.metric("Bottom Quartile", format_value(r["bottom_quartile"], r["unit"], r["format"]))

                # Position bar chart
                chart = create_metric_bar_chart(r)
                st.plotly_chart(chart, use_container_width=True)

                # Delta
                delta_pct = r["delta_pct"]
                direction_word = "above" if delta_pct > 0 else "below"
                st.markdown(
                    f"**Delta vs. Median:** {abs(delta_pct):.1f}% {direction_word} the industry median"
                )

                # Insight
                st.markdown(f"**Analysis:** {r['insight']}")

                # What this metric means
                bench = benchmarks.get(r["metric_id"], {})
                if "description" in bench:
                    st.caption(f"*{bench['description']}*")
                st.caption(f"Source: {r['source']}")

        st.divider()


show()
