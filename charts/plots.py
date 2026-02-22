"""
Chart builders using Plotly — radar, horizontal bar, and gauge charts.
"""
import plotly.graph_objects as go

# Consistent color scheme
COLORS = {
    "top_quartile": "#22c55e",      # green
    "above_median": "#86efac",      # light green
    "below_median": "#fbbf24",      # amber
    "bottom_quartile": "#ef4444",   # red
    "client": "#3b82f6",            # blue
    "median_line": "#6b7280",       # gray
    "top_q_line": "#22c55e",        # green
    "bottom_q_line": "#ef4444",     # red
    "background": "#f8fafc",
}

QUARTILE_LABELS = {
    "top_quartile": "Top Quartile",
    "above_median": "Above Median",
    "below_median": "Below Median",
    "bottom_quartile": "Bottom Quartile",
}


def create_radar_chart(results: list[dict], max_metrics: int = 12) -> go.Figure:
    """
    Create a radar/spider chart showing client scores vs median and top quartile.
    Scores are normalized 0-100.
    """
    # Use up to max_metrics for readability
    data = results[:max_metrics]
    if not data:
        return go.Figure()

    categories = [r["name"] for r in data]
    client_scores = [r["score"] for r in data]

    # Close the polygon
    categories_closed = categories + [categories[0]]
    client_closed = client_scores + [client_scores[0]]
    median_closed = [50] * len(categories) + [50]  # median is always 50 on normalized scale
    top_q_closed = [100] * len(categories) + [100]

    fig = go.Figure()

    # Top quartile reference (outer boundary)
    fig.add_trace(
        go.Scatterpolar(
            r=top_q_closed,
            theta=categories_closed,
            name="Top Quartile",
            line=dict(color=COLORS["top_q_line"], width=1, dash="dot"),
            fill=None,
            opacity=0.5,
        )
    )

    # Median reference
    fig.add_trace(
        go.Scatterpolar(
            r=median_closed,
            theta=categories_closed,
            name="Industry Median",
            line=dict(color=COLORS["median_line"], width=2, dash="dash"),
            fill=None,
        )
    )

    # Client data
    fig.add_trace(
        go.Scatterpolar(
            r=client_closed,
            theta=categories_closed,
            name="Your Organization",
            line=dict(color=COLORS["client"], width=3),
            fill="toself",
            fillcolor="rgba(59, 130, 246, 0.15)",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 105],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0", "25", "50", "75", "100"],
                gridcolor="#e2e8f0",
            ),
            angularaxis=dict(gridcolor="#e2e8f0"),
            bgcolor="white",
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        title=dict(
            text="IT Benchmarking Scorecard",
            x=0.5,
            font=dict(size=18),
        ),
        height=550,
        margin=dict(t=80, b=80, l=80, r=80),
    )

    return fig


def create_metric_bar_chart(result: dict) -> go.Figure:
    """
    Create a horizontal bar chart for a single metric showing the client value
    positioned against benchmark quartile ranges.
    """
    bench_tq = result["top_quartile"]
    bench_med = result["median"]
    bench_bq = result["bottom_quartile"]
    client_val = result["value"]
    direction = result["direction"]
    name = result["name"]
    unit = result["unit"]
    fmt = result["format"]

    # Determine the range for the chart
    all_vals = [bench_tq, bench_med, bench_bq, client_val]
    min_val = min(all_vals) * 0.8
    max_val = max(all_vals) * 1.2

    if direction == "lower_is_better":
        # Left is better: TQ < Median < BQ
        range_start = min_val
        range_end = max_val
    else:
        # Right is better: BQ < Median < TQ
        range_start = min_val
        range_end = max_val

    color = COLORS[result["quartile"]]

    fig = go.Figure()

    # Background quartile bands
    sorted_benchmarks = sorted([bench_tq, bench_med, bench_bq])
    band_colors = ["rgba(34,197,94,0.15)", "rgba(251,191,36,0.15)", "rgba(239,68,68,0.15)"]
    if direction == "higher_is_better":
        band_colors = list(reversed(band_colors))

    # Band 1: min to first benchmark
    fig.add_vrect(x0=range_start, x1=sorted_benchmarks[0], fillcolor=band_colors[0], layer="below", line_width=0)
    # Band 2: first to second benchmark
    fig.add_vrect(x0=sorted_benchmarks[0], x1=sorted_benchmarks[1], fillcolor=band_colors[1], layer="below", line_width=0)
    # Band 3: second to third benchmark
    fig.add_vrect(x0=sorted_benchmarks[1], x1=sorted_benchmarks[2], fillcolor=band_colors[1], layer="below", line_width=0)
    # Band 4: third benchmark to max
    fig.add_vrect(x0=sorted_benchmarks[2], x1=range_end, fillcolor=band_colors[2], layer="below", line_width=0)

    # Benchmark reference lines
    for val, label, dash in [
        (bench_tq, "Top Q", "dot"),
        (bench_med, "Median", "dash"),
        (bench_bq, "Bottom Q", "dot"),
    ]:
        fig.add_vline(
            x=val,
            line=dict(color="#94a3b8", width=1.5, dash=dash),
            annotation=dict(
                text=f"{label}: {val:{fmt}}{unit if unit == '%' else ''}",
                showarrow=False,
                yshift=10,
                font=dict(size=10, color="#64748b"),
            ),
        )

    # Client marker
    prefix = "$" if unit == "$" else ""
    suffix = "%" if unit == "%" else ""
    if unit == "ratio":
        client_label = f"You: 1:{client_val:.0f}"
    else:
        client_label = f"You: {prefix}{client_val:{fmt}}{suffix}"

    fig.add_trace(
        go.Scatter(
            x=[client_val],
            y=[0.5],
            mode="markers+text",
            marker=dict(size=18, color=color, symbol="diamond", line=dict(width=2, color="white")),
            text=[client_label],
            textposition="top center",
            textfont=dict(size=12, color=color),
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis=dict(range=[range_start, range_end], title=f"{unit}" if unit != "ratio" else "Users per IT FTE"),
        yaxis=dict(visible=False, range=[0, 1]),
        height=120,
        margin=dict(t=30, b=30, l=10, r=10),
        plot_bgcolor="white",
    )

    return fig


def create_summary_gauge(avg_score: float) -> go.Figure:
    """Create a gauge chart showing the overall benchmark score."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=avg_score,
            number=dict(suffix="/100", font=dict(size=36)),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=2),
                bar=dict(color=COLORS["client"], thickness=0.75),
                steps=[
                    dict(range=[0, 25], color="rgba(239,68,68,0.2)"),
                    dict(range=[25, 50], color="rgba(251,191,36,0.2)"),
                    dict(range=[50, 75], color="rgba(134,239,172,0.2)"),
                    dict(range=[75, 100], color="rgba(34,197,94,0.2)"),
                ],
                threshold=dict(
                    line=dict(color="#6b7280", width=3),
                    thickness=0.8,
                    value=50,
                ),
            ),
            title=dict(text="Overall Benchmark Score", font=dict(size=16)),
        )
    )

    fig.update_layout(
        height=250,
        margin=dict(t=50, b=10, l=30, r=30),
    )

    return fig


def create_category_bar_chart(results: list[dict]) -> go.Figure:
    """
    Create a horizontal bar chart showing all metrics with color-coded quartile positioning.
    """
    if not results:
        return go.Figure()

    names = [r["name"] for r in reversed(results)]
    scores = [r["score"] for r in reversed(results)]
    colors = [COLORS[r["quartile"]] for r in reversed(results)]
    quartile_labels = [QUARTILE_LABELS[r["quartile"]] for r in reversed(results)]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=names,
            x=scores,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=quartile_labels,
            textposition="auto",
            textfont=dict(color="white", size=11),
            hovertemplate="%{y}<br>Score: %{x:.0f}/100<br>%{text}<extra></extra>",
        )
    )

    # Median reference line
    fig.add_vline(
        x=50,
        line=dict(color="#6b7280", width=2, dash="dash"),
        annotation=dict(text="Median", showarrow=False, yshift=-15, font=dict(size=10)),
    )

    fig.update_layout(
        xaxis=dict(title="Benchmark Score (0-100)", range=[0, 105]),
        yaxis=dict(automargin=True),
        height=max(400, len(results) * 40),
        margin=dict(t=30, b=40, l=10, r=10),
        plot_bgcolor="white",
        title=dict(text="Metric-by-Metric Benchmark Positioning", x=0.5, font=dict(size=16)),
    )

    return fig
