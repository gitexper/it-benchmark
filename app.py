"""
IT Benchmarking Tool — Multi-Industry
Main entry point.
"""
import streamlit as st

st.set_page_config(
    page_title="IT Benchmark Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Navigation ─────────────────────────────────────────────────────
input_page = st.Page("pages/1_client_input.py", title="Client Input", icon="📋")
results_page = st.Page("pages/2_results.py", title="Results Dashboard", icon="📊")
detail_page = st.Page("pages/3_detailed_analysis.py", title="Detailed Analysis", icon="🔍")

nav = st.navigation([input_page, results_page, detail_page])

# ── Sidebar branding ───────────────────────────────────────────────
with st.sidebar:
    st.title("IT Benchmark")
    st.caption("Multi-Industry Edition")
    st.divider()

    if st.session_state.get("client_data"):
        name = st.session_state["client_data"].get("company_name", "")
        industry_name = st.session_state["client_data"].get("industry_name", "")
        if name:
            st.markdown(f"**Active Client:** {name}")
        if industry_name:
            st.markdown(f"**Industry:** {industry_name}")
        if st.button("Clear Data", use_container_width=True):
            for key in ["client_data", "analysis_run", "analysis_results"]:
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.markdown("*No client data loaded.*")

    st.divider()
    st.caption(
        "Benchmarks sourced from Gartner, Avasant, "
        "APQC, McKinsey, HIMSS, CHIME, KLAS, "
        "IANS Research, MetricNet. "
        "2024 baseline data."
    )

nav.run()
