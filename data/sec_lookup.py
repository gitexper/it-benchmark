"""
SEC EDGAR integration — company search, financial data extraction, and strategic context.
Uses the free SEC EDGAR APIs (no API key required).
"""
import re
import requests
from bs4 import BeautifulSoup

# SEC requires a User-Agent with contact info
SEC_HEADERS = {
    "User-Agent": "ITBenchmarkTool contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

# SIC code → industry mapping
SIC_INDUSTRY_MAP = {
    # Financial Services: SIC 6000-6999
    range(6000, 7000): "financial_services",
    # Healthcare: SIC 8000-8100
    range(8000, 8100): "healthcare",
}

# IT-relevant keyword phrases for strategic context extraction.
# These are multi-word phrases to reduce false positives from generic words like "technology".
IT_KEYWORDS = [
    # Spending / investment signals
    "technology spend", "technology investment", "IT spend", "IT investment",
    "technology budget", "tech spend", "invested in technology",
    "technology expenditure", "spent on technology",
    # Cloud & infrastructure
    "cloud computing", "cloud migration", "cloud infrastructure", "cloud-based",
    "public cloud", "private cloud", "hybrid cloud", "cloud services",
    "data center", "infrastructure modernization", "legacy systems",
    "application modernization", "systems modernization",
    # Cybersecurity
    "cybersecurity", "cyber security", "information security", "cyber threat",
    "ransomware", "data breach", "security incident", "cyber risk",
    "security posture", "zero trust",
    # AI & analytics
    "artificial intelligence", "machine learning", "generative AI", "GenAI",
    "data analytics", "advanced analytics", "predictive analytics",
    "large language model",
    # Digital & transformation
    "digital transformation", "digital strategy", "digital capabilities",
    "digital platform", "digital initiative",
    # IT operations & workforce
    "IT workforce", "IT operations", "IT outsourcing", "managed services",
    "technology vendor", "technology partner", "systems integration",
    "DevOps", "agile transformation", "enterprise architecture",
    "technology strategy", "technology platform", "technology modernization",
    "technology risk", "operational resilience", "technology resilience",
    # Software & SaaS
    "SaaS", "software-as-a-service", "software platform",
    "automation", "robotic process automation", "RPA",
]


def sic_to_industry(sic_code: str) -> str | None:
    """Map a SIC code to our industry keys. Returns None if no match."""
    try:
        sic = int(sic_code)
    except (ValueError, TypeError):
        return None
    for sic_range, industry in SIC_INDUSTRY_MAP.items():
        if sic in sic_range:
            return industry
    return None


def search_company(name: str) -> list[dict]:
    """
    Search SEC EDGAR for companies matching the given name.
    Uses company_tickers.json which contains only parent entities with tickers.
    Returns list of dicts: [{name, cik, ticker, sic, industry}]
    """
    if not name or len(name.strip()) < 2:
        return []

    search_term = name.strip().upper()

    # Primary: use company_tickers.json — only parent entities with tickers
    try:
        resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=SEC_HEADERS, timeout=10,
        )
        resp.raise_for_status()
        all_tickers = resp.json()
    except Exception:
        all_tickers = {}

    # Search by company name (fuzzy) and by ticker (exact)
    seen_ciks = set()
    results = []
    for entry in all_tickers.values():
        title = entry.get("title", "")
        ticker = entry.get("ticker", "")
        cik = str(entry.get("cik_str", ""))

        if not cik or cik in seen_ciks:
            continue

        # Match: search term in company name, or exact ticker match
        if search_term in title.upper() or search_term == ticker.upper():
            seen_ciks.add(cik)
            results.append({
                "name": title,
                "cik": cik,
                "ticker": ticker,
                "sic": "",
                "industry": None,
            })

        if len(results) >= 10:
            break

    # Enrich with SIC and industry from submissions endpoint (first 5 only for speed)
    for r in results[:5]:
        try:
            sub = _get_submissions(r["cik"])
            r["sic"] = sub.get("sic", "")
            r["industry"] = sic_to_industry(r["sic"])
            # Use official name from submissions if available
            if sub.get("name"):
                r["name"] = sub["name"]
        except Exception:
            pass

    return results


def _get_submissions(cik: str) -> dict:
    """Get company submissions/metadata from EDGAR."""
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    resp = requests.get(url, headers=SEC_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_financials(cik: str) -> dict:
    """
    Pull structured XBRL financial data from SEC EDGAR.
    Returns dict with: revenue, employees, operating_expenses, total_assets, fiscal_year
    """
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json"

    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"Could not fetch XBRL data: {e}"}

    facts = data.get("facts", {})
    us_gaap = facts.get("us-gaap", {})
    dei = facts.get("dei", {})

    result = {}

    # Revenue — try multiple XBRL tags
    revenue_tags = [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "InterestAndDividendIncomeOperating",  # banks
        "TotalRevenuesAndOtherIncome",
        "PremiumsEarnedNet",  # insurance
        "NetInterestIncome",  # banks fallback
    ]
    result["revenue"] = _get_latest_annual(us_gaap, revenue_tags)

    # Employees
    result["employees"] = _get_latest_annual(dei, ["EntityNumberOfEmployees"])

    # Operating Expenses
    opex_tags = [
        "OperatingExpenses",
        "CostsAndExpenses",
        "NoninterestExpense",  # banks
        "BenefitsLossesAndExpenses",  # insurance
        "OperatingCostsAndExpenses",
    ]
    result["operating_expenses"] = _get_latest_annual(us_gaap, opex_tags)

    # Total Assets
    result["total_assets"] = _get_latest_annual(us_gaap, ["Assets"])

    # Get the fiscal year from the most recent data point
    result["fiscal_year"] = _get_latest_fiscal_year(us_gaap, dei)

    # Get SIC and industry
    try:
        sub = _get_submissions(cik)
        result["sic"] = sub.get("sic", "")
        result["industry"] = sic_to_industry(result["sic"])
        result["company_name"] = sub.get("name", "")
        tickers = sub.get("tickers", [])
        result["ticker"] = tickers[0] if tickers else ""
    except Exception:
        pass

    return result


def _get_latest_annual(taxonomy: dict, tag_names: list[str]) -> int | None:
    """
    Extract the most recent annual (10-K) value for the first matching XBRL tag.
    Returns the value as an integer, or None if not found.
    """
    for tag in tag_names:
        concept = taxonomy.get(tag, {})
        units = concept.get("units", {})

        # Try USD first, then pure number (for employee count)
        for unit_type in ["USD", "pure", ""]:
            values = units.get(unit_type, [])
            if not values:
                # Try first available unit
                if units and not unit_type:
                    first_unit = list(units.keys())[0]
                    values = units[first_unit]
                continue

            # Filter for 10-K annual filings (form = "10-K") and full-year periods
            annual_values = []
            for v in values:
                form = v.get("form", "")
                if form in ("10-K", "10-K/A"):
                    # Prefer values with no "frame" that are full year (not quarterly)
                    start = v.get("start", "")
                    end = v.get("end", v.get("filed", ""))
                    # Full-year check: start and end should be ~12 months apart
                    annual_values.append(v)

            if annual_values:
                # Sort by end date descending to get most recent
                annual_values.sort(key=lambda x: x.get("end", x.get("filed", "")), reverse=True)
                val = annual_values[0].get("val")
                if val is not None:
                    return int(val)

    return None


def _get_latest_fiscal_year(us_gaap: dict, dei: dict) -> str:
    """Try to determine the latest fiscal year from available data."""
    # Check DocumentFiscalYearFocus first
    fiscal_year = dei.get("DocumentFiscalYearFocus", {})
    units = fiscal_year.get("units", {})
    for unit_values in units.values():
        if unit_values:
            sorted_vals = sorted(unit_values, key=lambda x: x.get("end", ""), reverse=True)
            if sorted_vals:
                return str(sorted_vals[0].get("val", ""))

    # Fallback: look at the most recent 10-K filing date
    for tag in ["Revenues", "Assets"]:
        concept = us_gaap.get(tag, {})
        for unit_values in concept.get("units", {}).values():
            annual = [v for v in unit_values if v.get("form") in ("10-K", "10-K/A")]
            if annual:
                annual.sort(key=lambda x: x.get("end", ""), reverse=True)
                end_date = annual[0].get("end", "")
                if end_date:
                    return end_date[:4]

    return "N/A"


def get_strategic_context(company_name: str, max_items: int = 5) -> list[dict]:
    """
    Find recent IT spending and technology strategy news for a company.
    Uses Google News RSS to find relevant articles.
    Returns a list of dicts: [{title, source, url, date}]
    """
    import warnings
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    # Clean up company name for search (remove Inc., Corp., etc.)
    clean_name = re.sub(r"\b(inc|corp|co|ltd|llc|plc|group|holdings)\b\.?", "", company_name, flags=re.IGNORECASE).strip()
    clean_name = re.sub(r"\s+", " ", clean_name).strip()
    # Remove trailing punctuation
    clean_name = clean_name.rstrip(" ,&/")

    # Search Google News RSS for IT/technology news about this company
    search_queries = [
        f"{clean_name} technology spending IT budget AI investment",
        f"{clean_name} cybersecurity cloud digital transformation",
    ]

    all_articles = []
    seen_titles = set()

    for query in search_queries:
        encoded = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all("item")

            for item in items[:15]:
                title_tag = item.find("title")
                raw_title = title_tag.text.strip() if title_tag else ""
                if not raw_title or raw_title.lower() in seen_titles:
                    continue

                # Google News titles end with " - Source Name"
                # Parse the source name from the title
                source_name = ""
                title = raw_title
                title_match = re.match(r"^(.+)\s+-\s+(.+)$", raw_title)
                if title_match:
                    title = title_match.group(1).strip()
                    source_name = title_match.group(2).strip()

                source_tag = item.find("source")
                source_url = source_tag.get("url", "") if source_tag else ""
                # Fallback: get source name from tag if not parsed from title
                if not source_name and source_tag and source_tag.next_sibling:
                    source_name = str(source_tag.next_sibling).strip()

                pubdate_tag = item.find("pubdate")
                date_str = pubdate_tag.text.strip() if pubdate_tag else ""

                # Filter: title must mention the company (at least partially)
                name_parts = clean_name.upper().split()
                first_word = name_parts[0] if name_parts else ""
                if first_word and first_word not in raw_title.upper():
                    continue

                seen_titles.add(raw_title.lower())
                all_articles.append({
                    "title": title,
                    "source": source_name,
                    "url": source_url,
                    "date": date_str,
                })
        except Exception:
            continue

    if not all_articles:
        return []

    # Return the top N most recent (they come sorted by relevance from Google)
    return all_articles[:max_items]
