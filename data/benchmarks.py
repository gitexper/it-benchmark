"""
IT Benchmarking Data — Multi-Industry
Sources: Gartner, Avasant/Computer Economics, APQC, McKinsey, IANS Research,
         MetricNet, HIMSS, CHIME, KLAS, Definitive Healthcare
All figures represent 2024 baseline data.
"""

# ── Available Industries ───────────────────────────────────────────
INDUSTRIES = {
    "financial_services": {
        "name": "Financial Services",
        "sub_verticals": ["Banking", "Insurance", "Asset Management", "Fintech", "Other"],
    },
    "healthcare": {
        "name": "Healthcare",
        "sub_verticals": ["Hospital / Health System", "Health Plan / Payer", "Physician Practice", "Life Sciences", "Other"],
    },
}

# ── Metric Definitions (shared across industries) ──────────────────
METRIC_DEFINITIONS = {
    "it_spend_pct_revenue": {
        "name": "IT Spend as % of Revenue",
        "category": "Spend",
        "unit": "%",
        "format": ".1f",
        "direction": "lower_is_better",
        "description": "Total IT budget divided by annual revenue.",
    },
    "it_spend_per_employee": {
        "name": "IT Spend per Employee",
        "category": "Spend",
        "unit": "$",
        "format": ",.0f",
        "direction": "lower_is_better",
        "description": "Total IT budget divided by total firm headcount.",
    },
    "it_spend_pct_opex": {
        "name": "IT Spend as % of OpEx",
        "category": "Spend",
        "unit": "%",
        "format": ".1f",
        "direction": "lower_is_better",
        "description": "Total IT budget as a share of total operating expenses.",
    },
    "it_budget_yoy_growth": {
        "name": "IT Budget Year-over-Year Growth",
        "category": "Spend",
        "unit": "%",
        "format": ".1f",
        "direction": "higher_is_better",
        "description": "Percentage increase in IT budget from prior year.",
    },
    "it_staff_pct_employees": {
        "name": "IT Staff as % of Total Employees",
        "category": "Staffing",
        "unit": "%",
        "format": ".1f",
        "direction": "lower_is_better",
        "description": "IT FTEs as a share of total firm headcount.",
    },
    "it_staffing_ratio": {
        "name": "IT Staffing Ratio (Users per IT FTE)",
        "category": "Staffing",
        "unit": "ratio",
        "format": ".0f",
        "direction": "lower_is_better",
        "description": "Number of total employees supported per IT FTE. Lower means more IT support per person.",
    },
    "run_budget_pct": {
        "name": "Run (Keep-the-Lights-On) Budget %",
        "category": "Budget Allocation",
        "unit": "%",
        "format": ".0f",
        "direction": "lower_is_better",
        "description": "Percentage of IT budget spent on maintaining existing operations.",
    },
    "grow_budget_pct": {
        "name": "Grow (Enhance) Budget %",
        "category": "Budget Allocation",
        "unit": "%",
        "format": ".0f",
        "direction": "higher_is_better",
        "description": "Percentage of IT budget spent on enhancing existing capabilities.",
    },
    "transform_budget_pct": {
        "name": "Transform (Innovation) Budget %",
        "category": "Budget Allocation",
        "unit": "%",
        "format": ".0f",
        "direction": "higher_is_better",
        "description": "Percentage of IT budget spent on transformative, new capability initiatives.",
    },
    "cloud_pct_budget": {
        "name": "Cloud Spend as % of IT Budget",
        "category": "Technology Mix",
        "unit": "%",
        "format": ".0f",
        "direction": "higher_is_better",
        "description": "Cloud expenditure (IaaS, PaaS, SaaS) as a share of total IT budget.",
    },
    "cybersecurity_pct_budget": {
        "name": "Cybersecurity Spend as % of IT Budget",
        "category": "Technology Mix",
        "unit": "%",
        "format": ".1f",
        "direction": "higher_is_better",
        "description": "Cybersecurity and information security spend as a share of IT budget.",
    },
    "it_labor_pct_budget": {
        "name": "IT Labor Cost as % of IT Budget",
        "category": "Cost Structure",
        "unit": "%",
        "format": ".0f",
        "direction": "lower_is_better",
        "description": "Internal IT labor costs (salaries, benefits) as a share of IT budget.",
    },
    "outsourcing_pct_budget": {
        "name": "Outsourcing Spend as % of IT Budget",
        "category": "Cost Structure",
        "unit": "%",
        "format": ".0f",
        "direction": "higher_is_better",
        "description": "Outsourced IT services spend as a share of total IT budget.",
    },
    "app_pct_budget": {
        "name": "Application Spend % (vs Infrastructure)",
        "category": "Cost Structure",
        "unit": "%",
        "format": ".0f",
        "direction": "higher_is_better",
        "description": "Application spend as a share of combined application + infrastructure spend.",
    },
    "system_availability": {
        "name": "Core System Availability",
        "category": "Operations",
        "unit": "%",
        "format": ".2f",
        "direction": "higher_is_better",
        "description": "Average uptime of mission-critical systems.",
    },
    "it_attrition_rate": {
        "name": "IT Employee Attrition Rate",
        "category": "Operations",
        "unit": "%",
        "format": ".0f",
        "direction": "lower_is_better",
        "description": "Annual voluntary turnover rate for IT staff.",
    },
    "helpdesk_cost_per_ticket": {
        "name": "Help Desk Cost per Ticket",
        "category": "Operations",
        "unit": "$",
        "format": ",.0f",
        "direction": "lower_is_better",
        "description": "Average fully-loaded cost to resolve a Tier 1 help desk ticket.",
    },
}

# ── Industry-Specific Benchmark Values & Insights ──────────────────
# Each industry has: top_quartile, median, bottom_quartile, insight_high, insight_low, insight_aligned, source

INDUSTRY_BENCHMARKS = {
    # ================================================================
    # FINANCIAL SERVICES
    # ================================================================
    "financial_services": {
        "it_spend_pct_revenue": {
            "top_quartile": 5.7, "median": 7.9, "bottom_quartile": 11.4,
            "insight_high": "You are spending significantly more on IT relative to revenue than peers. This may indicate inefficiency, technical debt, or a strategic heavy-investment phase.",
            "insight_low": "Your IT spend is lean relative to revenue. Verify this isn't creating underinvestment risk in security, modernization, or talent.",
            "insight_aligned": "Your IT spend as a percentage of revenue is well-aligned with Financial Services peers.",
            "source": "Gartner / Avasant Computer Economics",
        },
        "it_spend_per_employee": {
            "top_quartile": 18_000, "median": 35_000, "bottom_quartile": 55_000,
            "insight_high": "Your per-employee IT cost is above the median. Check for over-provisioning, license waste, or high support costs.",
            "insight_low": "You are spending less per employee than peers. Ensure end-user experience and productivity tooling are not suffering.",
            "insight_aligned": "Your per-employee IT spend is in line with Financial Services norms.",
            "source": "Gartner / SouthState",
        },
        "it_spend_pct_opex": {
            "top_quartile": 8.5, "median": 11.2, "bottom_quartile": 15.0,
            "insight_high": "IT is consuming a large share of operating expenses. Evaluate whether this reflects strategic investment or cost inefficiency.",
            "insight_low": "IT's share of OpEx is low. This could indicate efficiency or potential underinvestment.",
            "insight_aligned": "Your IT share of operating expenses is typical for the industry.",
            "source": "Gartner / SouthState",
        },
        "it_budget_yoy_growth": {
            "top_quartile": 8.0, "median": 4.7, "bottom_quartile": 2.0,
            "insight_high": "Aggressive budget growth signals strong organizational commitment to technology.",
            "insight_low": "Flat or declining IT budgets may constrain your ability to modernize and compete.",
            "insight_aligned": "Your budget growth rate is typical for Financial Services firms.",
            "source": "Gartner / SouthState",
        },
        "it_staff_pct_employees": {
            "top_quartile": 8.0, "median": 12.3, "bottom_quartile": 17.0,
            "insight_high": "Your IT headcount ratio is above the median. Evaluate whether automation, outsourcing, or process improvement could reduce this.",
            "insight_low": "Your IT staffing is lean. Ensure critical capabilities (security, architecture) are not understaffed.",
            "insight_aligned": "Your IT staffing ratio is typical for Financial Services.",
            "source": "Gartner / GoWorkWize",
        },
        "it_staffing_ratio": {
            "top_quartile": 50, "median": 70, "bottom_quartile": 100,
            "insight_high": "Each IT person supports many users. You may be understaffed relative to peers, risking service quality.",
            "insight_low": "You have rich IT support coverage per employee. Verify this level of investment is delivering proportional value.",
            "insight_aligned": "Your IT support ratio is well-aligned with industry peers.",
            "source": "GoWorkWize / TalentMSH",
        },
        "run_budget_pct": {
            "top_quartile": 55, "median": 67, "bottom_quartile": 78,
            "insight_high": "A high Run budget leaves little room for innovation. Consider modernization to free up capacity.",
            "insight_low": "You are keeping Run costs low, freeing budget for growth and transformation. Strong position.",
            "insight_aligned": "Your Run allocation is typical — most firms spend about two-thirds maintaining existing systems.",
            "source": "Gartner / SouthState",
        },
        "grow_budget_pct": {
            "top_quartile": 27, "median": 22, "bottom_quartile": 15,
            "insight_high": "Strong Grow investment — you are actively enhancing capabilities ahead of peers.",
            "insight_low": "Your Grow allocation is below peers. Existing capabilities may fall behind competitive expectations.",
            "insight_aligned": "Your Grow allocation is in line with industry norms.",
            "source": "Gartner / SouthState",
        },
        "transform_budget_pct": {
            "top_quartile": 18, "median": 11, "bottom_quartile": 7,
            "insight_high": "You are investing heavily in transformation — a strong signal of digital maturity.",
            "insight_low": "Low Transform spending may indicate limited innovation pipeline or excessive technical debt consuming resources.",
            "insight_aligned": "Your Transform investment is in the typical range for Financial Services.",
            "source": "Gartner / SouthState",
        },
        "cloud_pct_budget": {
            "top_quartile": 40, "median": 32, "bottom_quartile": 20,
            "insight_high": "You are cloud-forward relative to peers. Ensure you have strong FinOps practices to manage cloud cost growth.",
            "insight_low": "Your cloud adoption is below the median. Legacy infrastructure may be dragging on agility and cost efficiency.",
            "insight_aligned": "Your cloud investment is on par with Financial Services peers.",
            "source": "Gartner / DataStackHub",
        },
        "cybersecurity_pct_budget": {
            "top_quartile": 14.0, "median": 9.6, "bottom_quartile": 6.0,
            "insight_high": "Strong security investment. Ensure spend is outcome-driven, not just compliance-driven.",
            "insight_low": "Your security spend is below the median — a risk flag in a highly regulated, highly targeted industry.",
            "insight_aligned": "Your cybersecurity investment is in the typical range for Financial Services.",
            "source": "IANS Research / Deloitte",
        },
        "it_labor_pct_budget": {
            "top_quartile": 30, "median": 38, "bottom_quartile": 48,
            "insight_high": "Labor is consuming a large share of budget. Consider automation, offshore leverage, or managed services.",
            "insight_low": "Lean labor costs — verify this isn't creating key-person risk or quality issues.",
            "insight_aligned": "Your IT labor cost ratio is typical for the industry.",
            "source": "Gartner / SouthState",
        },
        "outsourcing_pct_budget": {
            "top_quartile": 30, "median": 18, "bottom_quartile": 10,
            "insight_high": "High outsourcing leverage can improve cost efficiency but watch for vendor dependency and knowledge loss.",
            "insight_low": "Low outsourcing may mean higher internal costs but better control. Evaluate selective outsourcing for commodity functions.",
            "insight_aligned": "Your outsourcing level is typical for Financial Services.",
            "source": "Gartner / ConnectBit",
        },
        "app_pct_budget": {
            "top_quartile": 65, "median": 60, "bottom_quartile": 50,
            "insight_high": "Strong application investment relative to infrastructure — consistent with modern, cloud-native strategies.",
            "insight_low": "Infrastructure-heavy spending may indicate legacy on-prem footprint. Consider cloud migration to shift spend toward applications.",
            "insight_aligned": "Your application vs. infrastructure balance is in line with industry trends.",
            "source": "McKinsey",
        },
        "system_availability": {
            "top_quartile": 99.99, "median": 99.95, "bottom_quartile": 99.90,
            "insight_high": "Excellent availability — you are at or near four-nines, which is the gold standard.",
            "insight_low": "Your availability is below the median. In Financial Services, even small downtime gaps translate to material revenue and reputational risk.",
            "insight_aligned": "Your availability is on par with industry norms.",
            "source": "Industry standard SLA benchmarks",
        },
        "it_attrition_rate": {
            "top_quartile": 10, "median": 15, "bottom_quartile": 22,
            "insight_high": "High attrition is costly and risks institutional knowledge loss. Review compensation, culture, and career paths.",
            "insight_low": "Strong retention — a competitive advantage in the talent-scarce IT market.",
            "insight_aligned": "Your IT attrition is in the typical range for Financial Services.",
            "source": "Payscale / BambooHR",
        },
        "helpdesk_cost_per_ticket": {
            "top_quartile": 12, "median": 22, "bottom_quartile": 40,
            "insight_high": "Your cost per ticket is above the median. Look at self-service adoption, knowledge base quality, and first-call resolution rates.",
            "insight_low": "Efficient help desk operations. Verify quality metrics (CSAT, FCR) are also strong.",
            "insight_aligned": "Your help desk cost is in the typical range for the industry.",
            "source": "MetricNet / HDI",
        },
    },

    # ================================================================
    # HEALTHCARE
    # ================================================================
    "healthcare": {
        "it_spend_pct_revenue": {
            "top_quartile": 3.0, "median": 3.8, "bottom_quartile": 5.0,
            "insight_high": "You are spending significantly more on IT relative to revenue than healthcare peers. This may reflect EHR modernization, regulatory burden, or inefficiency.",
            "insight_low": "Your IT spend is lean relative to revenue. In healthcare, underinvestment can create clinical safety and compliance risk.",
            "insight_aligned": "Your IT spend as a percentage of revenue is well-aligned with healthcare industry peers.",
            "source": "Avasant / Computer Economics / PEAKE",
        },
        "it_spend_per_employee": {
            "top_quartile": 6_000, "median": 8_500, "bottom_quartile": 12_000,
            "insight_high": "Your per-employee IT cost is above the median. Healthcare has large clinical workforces — check for license waste or over-provisioning.",
            "insight_low": "You are spending less per employee than peers. Ensure clinician productivity tools and EHR support are not suffering.",
            "insight_aligned": "Your per-employee IT spend is in line with healthcare norms.",
            "source": "Avasant / Computer Economics",
        },
        "it_spend_pct_opex": {
            "top_quartile": 2.0, "median": 2.8, "bottom_quartile": 3.5,
            "insight_high": "IT is consuming an above-average share of operating expenses. Healthcare OpEx is dominated by clinical labor — evaluate IT cost drivers.",
            "insight_low": "IT's share of OpEx is low. Given regulatory and cybersecurity demands, verify this isn't creating risk.",
            "insight_aligned": "Your IT share of operating expenses is typical for healthcare organizations.",
            "source": "Definitive Healthcare / Avasant",
        },
        "it_budget_yoy_growth": {
            "top_quartile": 10.0, "median": 6.0, "bottom_quartile": 3.0,
            "insight_high": "Aggressive budget growth signals strong organizational commitment to digital health and modernization.",
            "insight_low": "Flat IT budgets in healthcare are risky given rising cybersecurity threats and regulatory demands.",
            "insight_aligned": "Your budget growth rate is typical for healthcare organizations.",
            "source": "Gartner HCLS / Guidehouse",
        },
        "it_staff_pct_employees": {
            "top_quartile": 1.0, "median": 1.8, "bottom_quartile": 2.5,
            "insight_high": "Your IT headcount ratio is above the median. Healthcare has large non-IT workforces — evaluate whether outsourcing or automation could help.",
            "insight_low": "Your IT staffing is lean even for healthcare. Ensure EHR support, security, and clinical informatics are adequately covered.",
            "insight_aligned": "Your IT staffing ratio is typical for healthcare organizations.",
            "source": "Avasant / HIMSS",
        },
        "it_staffing_ratio": {
            "top_quartile": 50, "median": 60, "bottom_quartile": 100,
            "insight_high": "Each IT person supports many users. In healthcare, inadequate IT support directly impacts clinician productivity and patient safety.",
            "insight_low": "You have strong IT support coverage. Verify this is translating into better clinician experience and system reliability.",
            "insight_aligned": "Your IT support ratio is well-aligned with healthcare peers.",
            "source": "HIMSS / GoWorkWize",
        },
        "run_budget_pct": {
            "top_quartile": 55, "median": 63, "bottom_quartile": 72,
            "insight_high": "A high Run budget in healthcare often reflects legacy EHR maintenance and regulatory compliance burden. Evaluate modernization to free capacity.",
            "insight_low": "You are keeping Run costs low — strong position to invest in growth and transformation.",
            "insight_aligned": "Your Run allocation is typical for healthcare — regulatory and EHR maintenance consume significant budget.",
            "source": "Gartner RGT Framework",
        },
        "grow_budget_pct": {
            "top_quartile": 25, "median": 20, "bottom_quartile": 15,
            "insight_high": "Strong Grow investment — you are actively enhancing clinical and operational capabilities ahead of peers.",
            "insight_low": "Your Grow allocation is below peers. Clinical systems and patient experience platforms may fall behind.",
            "insight_aligned": "Your Grow allocation is in line with healthcare norms.",
            "source": "Gartner RGT Framework",
        },
        "transform_budget_pct": {
            "top_quartile": 15, "median": 12, "bottom_quartile": 8,
            "insight_high": "You are investing heavily in transformation — AI, virtual care, and digital front door initiatives set you apart.",
            "insight_low": "Low Transform spending may indicate limited innovation pipeline. Consider AI, telehealth, and interoperability investments.",
            "insight_aligned": "Your Transform investment is in the typical range for healthcare.",
            "source": "Gartner RGT Framework / CHIME",
        },
        "cloud_pct_budget": {
            "top_quartile": 25, "median": 16, "bottom_quartile": 10,
            "insight_high": "You are cloud-forward for healthcare. Ensure HIPAA-compliant cloud governance and FinOps practices are in place.",
            "insight_low": "Your cloud adoption is below the healthcare median. On-prem infrastructure may be limiting agility and interoperability.",
            "insight_aligned": "Your cloud investment is on par with healthcare peers.",
            "source": "Nutanix Healthcare ECI / Flexera",
        },
        "cybersecurity_pct_budget": {
            "top_quartile": 10.0, "median": 7.0, "bottom_quartile": 4.0,
            "insight_high": "Strong security investment — critical in healthcare given the rise in ransomware attacks on health systems.",
            "insight_low": "Your security spend is below the median — a serious risk flag. Healthcare is the #1 target for ransomware. Post-Change Healthcare breach, peers are investing heavily.",
            "insight_aligned": "Your cybersecurity investment is in the typical range for healthcare.",
            "source": "HIMSS Cybersecurity Survey / IANS Research",
        },
        "it_labor_pct_budget": {
            "top_quartile": 40, "median": 48, "bottom_quartile": 55,
            "insight_high": "Labor is consuming a large share of budget. Healthcare IT requires specialized skills (clinical informatics, EHR analysts) — evaluate managed services for commodity functions.",
            "insight_low": "Lean labor costs — verify clinical IT support and 24/7 coverage are not being compromised.",
            "insight_aligned": "Your IT labor cost ratio is typical for healthcare.",
            "source": "Avasant / ISG",
        },
        "outsourcing_pct_budget": {
            "top_quartile": 30, "median": 22, "bottom_quartile": 15,
            "insight_high": "High outsourcing leverage — common in healthcare for cybersecurity, infrastructure, and help desk. Watch for HIPAA compliance in vendor contracts.",
            "insight_low": "Low outsourcing may mean higher internal costs. Evaluate managed services for security, infrastructure, and service desk.",
            "insight_aligned": "Your outsourcing level is typical for healthcare.",
            "source": "Deloitte GOS / ISG",
        },
        "app_pct_budget": {
            "top_quartile": 45, "median": 38, "bottom_quartile": 30,
            "insight_high": "Strong application investment — consistent with EHR optimization, clinical decision support, and patient engagement platforms.",
            "insight_low": "Infrastructure-heavy spending may indicate aging on-prem data centers. Consider cloud migration to shift investment toward clinical applications.",
            "insight_aligned": "Your application vs. infrastructure balance is in line with healthcare trends.",
            "source": "HG Insights / Bain-KLAS",
        },
        "system_availability": {
            "top_quartile": 99.99, "median": 99.95, "bottom_quartile": 99.90,
            "insight_high": "Excellent availability — critical for patient safety. You are at or near four-nines.",
            "insight_low": "Your availability is below the median. In healthcare, EHR/clinical system downtime directly impacts patient care and safety.",
            "insight_aligned": "Your availability is on par with healthcare industry norms.",
            "source": "MetricNet / Healthcare SLA standards",
        },
        "it_attrition_rate": {
            "top_quartile": 10, "median": 14, "bottom_quartile": 18,
            "insight_high": "High attrition is especially costly in healthcare IT where EHR expertise and clinical workflow knowledge are hard to replace.",
            "insight_low": "Strong retention — a competitive advantage given the shortage of healthcare IT talent.",
            "insight_aligned": "Your IT attrition is in the typical range for healthcare.",
            "source": "LinkedIn / BLS / BambooHR",
        },
        "helpdesk_cost_per_ticket": {
            "top_quartile": 18, "median": 30, "bottom_quartile": 45,
            "insight_high": "Your cost per ticket is above the median. Healthcare tickets are complex (EHR, clinical devices) — look at self-service portals and knowledge bases.",
            "insight_low": "Efficient help desk operations for healthcare. Verify clinician satisfaction and first-call resolution are also strong.",
            "insight_aligned": "Your help desk cost is in the typical range for healthcare.",
            "source": "MetricNet / HDI / Medsphere",
        },
    },
}


def get_benchmarks(industry: str) -> dict:
    """
    Build the full benchmark dict for a given industry by merging
    metric definitions with industry-specific values.
    """
    industry_data = INDUSTRY_BENCHMARKS.get(industry, {})
    result = {}
    for metric_id, definition in METRIC_DEFINITIONS.items():
        if metric_id in industry_data:
            merged = {**definition, **industry_data[metric_id]}
            result[metric_id] = merged
    return result


# Ordered list of metric keys for consistent display
METRIC_ORDER = [
    "it_spend_pct_revenue",
    "it_spend_per_employee",
    "it_spend_pct_opex",
    "it_budget_yoy_growth",
    "it_staff_pct_employees",
    "it_staffing_ratio",
    "run_budget_pct",
    "grow_budget_pct",
    "transform_budget_pct",
    "cloud_pct_budget",
    "cybersecurity_pct_budget",
    "it_labor_pct_budget",
    "outsourcing_pct_budget",
    "app_pct_budget",
    "system_availability",
    "it_attrition_rate",
    "helpdesk_cost_per_ticket",
]

# Category display order
CATEGORIES = [
    "Spend",
    "Staffing",
    "Budget Allocation",
    "Technology Mix",
    "Cost Structure",
    "Operations",
]
