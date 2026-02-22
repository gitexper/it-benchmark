"""
Page 1: Client Data Input Form
"""
import streamlit as st
from data.benchmarks import INDUSTRIES
from data.sec_lookup import search_company, get_financials, get_strategic_context, sic_to_industry


def _format_dollars(val):
    """Format a large dollar amount for display."""
    if val is None:
        return "N/A"
    if val >= 1_000_000_000:
        return f"${val / 1_000_000_000:,.1f}B"
    elif val >= 1_000_000:
        return f"${val / 1_000_000:,.0f}M"
    else:
        return f"${val:,.0f}"


def show():
    st.header("Client Data Input")
    st.markdown(
        "Enter your client's IT metrics below. All dollar values in USD. "
        "The analysis will compare these against industry benchmarks."
    )

    # ── SEC Lookup Section ─────────────────────────────────────────
    st.subheader("Company Lookup")
    st.caption(
        "Public companies: search SEC EDGAR to auto-fill financials. Private companies: skip and enter manually.  \n"
        "Industry auto-detection currently supports **Financial Services** and **Healthcare**. "
        "Other industries will still pull financials but you'll need to select the industry manually."
    )

    lookup_col1, lookup_col2 = st.columns([3, 1])
    with lookup_col1:
        search_name = st.text_input(
            "Search Company Name",
            value=st.session_state.get("search_name", ""),
            placeholder="e.g., JPMorgan, UnitedHealth, Wells Fargo...",
            key="search_input",
        )
    with lookup_col2:
        st.markdown("")  # vertical spacer
        lookup_clicked = st.button("Search SEC Filing", type="primary", use_container_width=True)

    # Handle search
    if lookup_clicked and search_name:
        st.session_state["search_name"] = search_name
        with st.spinner("Searching SEC EDGAR..."):
            results = search_company(search_name)
            st.session_state["sec_search_results"] = results
            st.session_state["sec_selected"] = None
            st.session_state["sec_financials"] = None
            st.session_state["sec_context"] = None

    # Show search results
    if st.session_state.get("sec_search_results"):
        results = st.session_state["sec_search_results"]
        if not results:
            st.warning("No SEC filings found. Enter data manually below.")
        else:
            options = [f"{r['name']}" + (f" ({r['ticker']})" if r.get('ticker') else "") for r in results]
            selected_idx = st.selectbox(
                "Select Company",
                range(len(options)),
                format_func=lambda i: options[i],
                key="company_select",
            )

            if selected_idx is not None:
                selected = results[selected_idx]
                cik = selected["cik"]

                # Only fetch if we haven't already for this CIK
                if st.session_state.get("sec_selected_cik") != cik:
                    with st.spinner("Pulling financials from latest 10-K..."):
                        financials = get_financials(cik)
                        context = get_strategic_context(cik)
                        st.session_state["sec_selected_cik"] = cik
                        st.session_state["sec_financials"] = financials
                        st.session_state["sec_context"] = context

                        # Pre-fill session state for form defaults
                        prefill = st.session_state.get("sec_prefill", {})
                        prefill["company_name"] = financials.get("company_name", selected["name"])
                        if financials.get("revenue"):
                            prefill["revenue"] = financials["revenue"]
                        if financials.get("employees"):
                            prefill["total_employees"] = financials["employees"]
                        if financials.get("operating_expenses"):
                            prefill["total_opex"] = financials["operating_expenses"]

                        # Auto-detect industry from SIC
                        detected_industry = financials.get("industry") or selected.get("industry")
                        if detected_industry:
                            prefill["industry"] = detected_industry

                        st.session_state["sec_prefill"] = prefill
                        st.rerun()

    # Show pre-filled info
    financials = st.session_state.get("sec_financials")
    if financials and not financials.get("error"):
        fiscal_year = financials.get("fiscal_year", "N/A")
        rev = _format_dollars(financials.get("revenue"))
        emp = f"{financials.get('employees', 'N/A'):,}" if financials.get("employees") else "N/A"
        opex = _format_dollars(financials.get("operating_expenses"))
        assets = _format_dollars(financials.get("total_assets"))

        st.success(
            f"**Pre-filled from {fiscal_year} 10-K:** "
            f"Revenue {rev}  |  Employees {emp}  |  OpEx {opex}  |  Total Assets {assets}"
        )

        # Strategic context
        context = st.session_state.get("sec_context", [])
        if context and context[0] != "No IT-relevant strategic context found in the latest 10-K.":
            with st.expander("Strategic Context from 10-K (IT-relevant excerpts)", expanded=False):
                for i, item in enumerate(context, 1):
                    st.markdown(f"{i}. {item}")
    elif financials and financials.get("error"):
        st.warning(f"Could not pull financials: {financials['error']}")

    st.divider()

    # ── Industry selector ──────────────────────────────────────────
    # Auto-detect from SEC or let user pick
    prefill = st.session_state.get("sec_prefill", {})
    detected_industry = prefill.get("industry")

    industry_keys = list(INDUSTRIES.keys())
    industry_names = [INDUSTRIES[k]["name"] for k in industry_keys]

    if detected_industry and detected_industry in industry_keys:
        default_idx = industry_keys.index(detected_industry)
        auto_label = f" (auto-detected from SEC filing)"
    else:
        default_idx = 0
        auto_label = ""

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_industry_name = st.selectbox(
            f"Industry{auto_label}",
            industry_names,
            index=default_idx,
        )
        selected_industry = industry_keys[industry_names.index(selected_industry_name)]
    with col2:
        sub_verticals = INDUSTRIES[selected_industry]["sub_verticals"]
        sub_vertical = st.selectbox("Sub-Vertical", sub_verticals, index=0)
    with col3:
        st.markdown("")

    st.divider()

    # ── Main Input Form ────────────────────────────────────────────
    with st.form("client_input_form"):
        st.subheader("Company Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            company_name = st.text_input(
                "Company Name",
                value=prefill.get("company_name", st.session_state.get("client_data", {}).get("company_name", "")),
            )
        with col2:
            revenue = st.number_input(
                "Annual Revenue ($)",
                min_value=0,
                value=prefill.get("revenue", st.session_state.get("client_data", {}).get("revenue", 0)),
                step=1_000_000,
                format="%d",
                help="Total annual revenue in USD",
            )
        with col3:
            total_employees = st.number_input(
                "Total Employees",
                min_value=0,
                value=prefill.get("total_employees", st.session_state.get("client_data", {}).get("total_employees", 0)),
                step=100,
                format="%d",
                help="Total firm headcount (not just IT)",
            )

        st.divider()

        # ── IT Spend ──────────────────────────────────────────────
        st.subheader("IT Spend")

        col1, col2, col3 = st.columns(3)
        with col1:
            it_budget = st.number_input(
                "Total IT Budget ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("it_budget", 0),
                step=100_000,
                format="%d",
            )
            it_budget_prior = st.number_input(
                "IT Budget Prior Year ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("it_budget_prior_year", 0),
                step=100_000,
                format="%d",
                help="For YoY growth calculation",
            )
        with col2:
            total_opex = st.number_input(
                "Total Operating Expenses ($)",
                min_value=0,
                value=prefill.get("total_opex", st.session_state.get("client_data", {}).get("total_opex", 0)),
                step=1_000_000,
                format="%d",
                help="Total firm operating expenses",
            )
            cloud_spend = st.number_input(
                "Cloud Spend ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("cloud_spend", 0),
                step=100_000,
                format="%d",
                help="IaaS + PaaS + SaaS spend",
            )
        with col3:
            cybersecurity_spend = st.number_input(
                "Cybersecurity Spend ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("cybersecurity_spend", 0),
                step=100_000,
                format="%d",
            )
            it_labor_cost = st.number_input(
                "IT Labor Costs ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("it_labor_cost", 0),
                step=100_000,
                format="%d",
                help="Internal IT salaries + benefits",
            )

        col1, col2 = st.columns(2)
        with col1:
            outsourcing_spend = st.number_input(
                "Outsourcing Spend ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("outsourcing_spend", 0),
                step=100_000,
                format="%d",
            )
            application_spend = st.number_input(
                "Application Spend ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("application_spend", 0),
                step=100_000,
                format="%d",
                help="Application development, licensing, maintenance",
            )
        with col2:
            infrastructure_spend = st.number_input(
                "Infrastructure Spend ($)",
                min_value=0,
                value=st.session_state.get("client_data", {}).get("infrastructure_spend", 0),
                step=100_000,
                format="%d",
                help="Servers, network, data center, hosting",
            )

        st.divider()

        # ── Budget Allocation ──────────────────────────────────────
        st.subheader("Budget Allocation (Run / Grow / Transform)")
        st.caption("Should sum to 100%. These represent the percentage of IT budget in each category.")

        col1, col2, col3 = st.columns(3)
        with col1:
            run_pct = st.number_input(
                "Run %",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("client_data", {}).get("run_pct", 0) or 0),
                step=1.0,
                help="Keep-the-lights-on operations",
            )
        with col2:
            grow_pct = st.number_input(
                "Grow %",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("client_data", {}).get("grow_pct", 0) or 0),
                step=1.0,
                help="Enhance existing capabilities",
            )
        with col3:
            transform_pct = st.number_input(
                "Transform %",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("client_data", {}).get("transform_pct", 0) or 0),
                step=1.0,
                help="New, transformative initiatives",
            )

        rgt_total = run_pct + grow_pct + transform_pct
        if rgt_total > 0 and abs(rgt_total - 100) > 1:
            st.warning(f"Run + Grow + Transform = {rgt_total:.0f}% (should be 100%)")

        st.divider()

        # ── IT Staffing ────────────────────────────────────────────
        st.subheader("IT Staffing")
        it_ftes = st.number_input(
            "Total IT FTEs",
            min_value=0,
            value=st.session_state.get("client_data", {}).get("it_ftes", 0),
            step=10,
            format="%d",
            help="Full-time equivalent IT staff (internal only)",
        )

        st.divider()

        # ── Operations ─────────────────────────────────────────────
        st.subheader("Operational Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            system_availability = st.number_input(
                "Core System Availability (%)",
                min_value=90.0,
                max_value=100.0,
                value=float(st.session_state.get("client_data", {}).get("system_availability", 99.95)),
                step=0.01,
                format="%.2f",
                help="Average uptime of core systems",
            )
        with col2:
            helpdesk_cost = st.number_input(
                "Help Desk Cost per Ticket ($)",
                min_value=0.0,
                value=float(st.session_state.get("client_data", {}).get("helpdesk_cost_per_ticket", 0) or 0),
                step=1.0,
                format="%.0f",
            )
        with col3:
            attrition = st.number_input(
                "IT Staff Attrition Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.get("client_data", {}).get("it_attrition_rate", 0) or 0),
                step=0.5,
                format="%.1f",
            )

        st.divider()

        # ── Submit ─────────────────────────────────────────────────
        submitted = st.form_submit_button(
            "Run Benchmark Analysis",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            errors = []
            if not company_name:
                errors.append("Company name is required.")
            if revenue <= 0:
                errors.append("Revenue must be greater than 0.")
            if total_employees <= 0:
                errors.append("Total employees must be greater than 0.")
            if it_budget <= 0:
                errors.append("IT budget must be greater than 0.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                client_data = {
                    "company_name": company_name,
                    "industry": selected_industry,
                    "industry_name": selected_industry_name,
                    "sub_vertical": sub_vertical,
                    "revenue": revenue,
                    "total_employees": total_employees,
                    "it_budget": it_budget,
                    "it_budget_prior_year": it_budget_prior,
                    "total_opex": total_opex,
                    "cloud_spend": cloud_spend,
                    "cybersecurity_spend": cybersecurity_spend,
                    "it_labor_cost": it_labor_cost,
                    "outsourcing_spend": outsourcing_spend,
                    "application_spend": application_spend,
                    "infrastructure_spend": infrastructure_spend,
                    "run_pct": run_pct if run_pct > 0 else None,
                    "grow_pct": grow_pct if grow_pct > 0 else None,
                    "transform_pct": transform_pct if transform_pct > 0 else None,
                    "it_ftes": it_ftes,
                    "system_availability": system_availability,
                    "helpdesk_cost_per_ticket": helpdesk_cost if helpdesk_cost > 0 else None,
                    "it_attrition_rate": attrition if attrition > 0 else None,
                }
                st.session_state["client_data"] = client_data
                st.session_state["analysis_run"] = True
                st.success(
                    f"Data saved for **{company_name}** ({selected_industry_name}). "
                    "Navigate to **Results Dashboard** to see the analysis."
                )


show()
