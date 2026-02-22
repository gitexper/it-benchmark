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

# IT-relevant keywords for strategic context extraction
IT_KEYWORDS = [
    "technology", "cybersecurity", "cyber security", "cloud computing", "cloud migration",
    "digital transformation", "artificial intelligence", "machine learning",
    "automation", "data analytics", "software", "infrastructure modernization",
    "information security", "data center", "SaaS", "IT spending", "IT investment",
    "technology budget", "tech spend", "information technology",
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
    Returns list of dicts: [{name, cik, ticker, sic, industry}]
    """
    if not name or len(name.strip()) < 2:
        return []

    # Use the EDGAR full-text search to find companies with 10-K filings
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": f'"{name}"',
        "dateRange": "custom",
        "startdt": "2023-01-01",
        "forms": "10-K",
    }

    try:
        resp = requests.get(url, params=params, headers=SEC_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        # Fallback: try the company tickers JSON
        return _search_company_fallback(name)

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return _search_company_fallback(name)

    # Deduplicate by CIK
    seen_ciks = set()
    results = []
    for hit in hits[:20]:
        source = hit.get("_source", {})
        cik = str(source.get("entity_id", "")).lstrip("0")
        if not cik or cik in seen_ciks:
            continue
        seen_ciks.add(cik)
        entity_name = source.get("display_names", [source.get("entity_name", name)])[0]
        results.append({
            "name": entity_name,
            "cik": cik,
            "ticker": "",
            "sic": "",
            "industry": None,
        })

    # Enrich with SIC from submissions endpoint (for first 5 results)
    for r in results[:5]:
        try:
            sub = _get_submissions(r["cik"])
            r["sic"] = sub.get("sic", "")
            r["industry"] = sic_to_industry(r["sic"])
            tickers = sub.get("tickers", [])
            if tickers:
                r["ticker"] = tickers[0]
        except Exception:
            pass

    return results[:10]


def _search_company_fallback(name: str) -> list[dict]:
    """Fallback search using the company tickers endpoint."""
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "company": name,
        "CIK": "",
        "type": "10-K",
        "dateb": "",
        "owner": "include",
        "count": "10",
        "search_text": "",
        "action": "getcompany",
        "output": "atom",
    }
    try:
        resp = requests.get(url, params=params, headers=SEC_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        entries = soup.find_all("entry")
        results = []
        for entry in entries[:10]:
            title = entry.find("title")
            if not title:
                continue
            text = title.get_text()
            # Parse "COMPANY NAME (CIK)" format
            match = re.match(r"(.+?)\s*\((\d+)\)", text)
            if match:
                company_name = match.group(1).strip()
                cik = match.group(2)
            else:
                company_name = text.strip()
                cik_tag = entry.find("cik")
                cik = cik_tag.get_text() if cik_tag else ""

            if cik:
                results.append({
                    "name": company_name,
                    "cik": cik.lstrip("0"),
                    "ticker": "",
                    "sic": "",
                    "industry": None,
                })
        return results
    except Exception:
        return []


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

    # Parse HTML and extract text
    soup = BeautifulSoup(text, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True)

    # Clean up whitespace
    full_text = re.sub(r"\s+", " ", full_text)

    # Extract sentences containing IT-relevant keywords
    # Split into sentences (rough heuristic)
    sentences = re.split(r"(?<=[.!?])\s+", full_text)

    relevant = []
    seen_snippets = set()
    keyword_pattern = re.compile(
        "|".join(re.escape(kw) for kw in IT_KEYWORDS),
        re.IGNORECASE,
    )

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 40 or len(sentence) > 500:
            continue

        if keyword_pattern.search(sentence):
            # Check for duplicates (fuzzy)
            snippet_key = sentence[:80].lower()
            if snippet_key not in seen_snippets:
                seen_snippets.add(snippet_key)
                # Score by number of keyword matches
                match_count = len(keyword_pattern.findall(sentence))
                relevant.append((match_count, sentence))

    # Sort by relevance (most keyword matches first)
    relevant.sort(key=lambda x: x[0], reverse=True)

    # Return top N
    results = [item[1] for item in relevant[:max_items]]

    if not results:
        return ["No IT-relevant strategic context found in the latest 10-K."]

    return results
