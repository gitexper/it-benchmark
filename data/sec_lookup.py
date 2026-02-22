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


def get_strategic_context(cik: str, max_items: int = 5) -> list[str]:
    """
    Extract IT-relevant strategic context from the latest 10-K filing.
    Returns a list of relevant text excerpts.
    """
    try:
        sub = _get_submissions(cik)
    except Exception:
        return ["Could not retrieve filing information."]

    # Find the most recent 10-K filing
    recent = sub.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    filing_url = None
    for i, form in enumerate(forms):
        if form in ("10-K", "10-K/A"):
            accession = accessions[i].replace("-", "")
            doc = primary_docs[i]
            padded_cik = cik.zfill(10)
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{padded_cik}/{accession}/{doc}"
            break

    if not filing_url:
        return ["No 10-K filing found."]

    # Download the filing
    try:
        resp = requests.get(filing_url, headers=SEC_HEADERS, timeout=20)
        resp.raise_for_status()
        text = resp.text
    except Exception:
        return ["Could not download the 10-K filing."]

    # Parse HTML — strip tables first (they produce garbage text)
    soup = BeautifulSoup(text, "html.parser")
    for table in soup.find_all("table"):
        table.decompose()
    full_text = soup.get_text(separator=" ", strip=True)

    # Clean up whitespace
    full_text = re.sub(r"\s+", " ", full_text)

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", full_text)

    relevant = []
    seen_snippets = set()
    keyword_pattern = re.compile(
        "|".join(re.escape(kw) for kw in IT_KEYWORDS),
        re.IGNORECASE,
    )

    for sentence in sentences:
        sentence = sentence.strip()

        # Length filter — too short = heading, too long = run-on from bad HTML
        if len(sentence) < 50 or len(sentence) > 600:
            continue

        # Skip sentences that are mostly numbers/symbols (financial tables, ratios)
        alpha_chars = sum(1 for c in sentence if c.isalpha())
        if alpha_chars < len(sentence) * 0.5:
            continue

        # Skip boilerplate / legal language
        lower = sentence.lower()
        if any(skip in lower for skip in [
            "incorporated by reference", "item 1a", "item 1b",
            "table of contents", "form 10-k", "page ",
            "securities and exchange commission", "see note",
            "the following table", "basis points",
            "tier 1 capital", "tier 2 capital", "risk-weighted assets",
            "capital ratio", "the accompanying notes",
        ]):
            continue

        if keyword_pattern.search(sentence):
            # Check for duplicates
            snippet_key = sentence[:80].lower()
            if snippet_key not in seen_snippets:
                seen_snippets.add(snippet_key)

                # Truncate for display
                display = sentence
                if len(display) > 350:
                    display = display[:350].rsplit(" ", 1)[0] + "..."

                # Score: keyword matches + bonus for strategic language
                match_count = len(keyword_pattern.findall(sentence))
                # Bonus for sentences with spending/investment language
                if re.search(r"\$[\d,.]+\s*(billion|million|B|M)", sentence, re.IGNORECASE):
                    match_count += 2
                if re.search(r"invest(ed|ing|ment)|spend(ing)?|budget|commit", lower):
                    match_count += 1
                if re.search(r"strateg(y|ic)|priorit(y|ize)|initiative|transform", lower):
                    match_count += 1

                relevant.append((match_count, display))

    # Sort by relevance score
    relevant.sort(key=lambda x: x[0], reverse=True)

    # Return top N
    results = [item[1] for item in relevant[:max_items]]

    if not results:
        return ["No IT-relevant strategic context found in the latest 10-K."]

    return results
