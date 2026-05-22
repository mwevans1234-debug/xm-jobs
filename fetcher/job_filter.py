import re

# ── Title allowlist ────────────────────────────────────────────────────────
# Job title MUST contain at least one of these terms to be included.
# Multi-word phrases use substring matching; single tokens use word boundaries.

TITLE_ALLOWLIST = [
    # Customer-side roles
    "customer experience",
    "voice of customer",
    "customer insights",
    "customer listening",
    "customer feedback",
    "customer research manager",
    "customer research director",
    # Employee-side roles
    "employee experience",
    "employee insights",
    "employee listening",
    "employee feedback",
    "people insights",
    "workforce insights",
    "people analytics",
    # Short abbreviations (single tokens — word-boundary matched)
    "cx",
    "voc",
    "nps",
    "csat",
    # "experience + role type" patterns
    "experience management",
    "experience manager",
    "experience director",
    "experience analyst",
    "experience lead",
    "experience specialist",
    "experience program",
    "experience strategist",
    # Program / survey focused
    "feedback program",
    "survey program",
    "experience data",
]

# ── Title blocklist ────────────────────────────────────────────────────────
# Reject titles that pass the allowlist but are clearly the wrong domain.

TITLE_BLOCKLIST = [
    "ux designer",
    "ui designer",
    "ui/ux",
    "ux/ui",
    "user experience designer",
    "software engineer",
    "software developer",
    "web developer",
    "devops",
    "machine learning engineer",
    "data engineer",
]

# ── Competitor company blocklist ───────────────────────────────────────────
# Exclude jobs from XM platform vendors (Qualtrics is intentionally absent).

COMPETITOR_COMPANIES = [
    "medallia",
    "inmoment",
    "perceptyx",
    "forsta",
    "confirmit",
    "nice satmetrix",
    "satmetrix",
    "verint",
    "sprinklr",
    "birdeye",
    "alchemer",
    "surveymonkey",
    "momentive",
    "culture amp",
    "glint",
    "peakon",
]


def _matches(text, term):
    """Case-insensitive match. Word boundaries for single tokens, substring for phrases."""
    if " " in term:
        return term in text
    return bool(re.search(r"\b" + re.escape(term) + r"\b", text))


def is_relevant(title, company=""):
    """Return True if this job belongs on the board."""
    title_lower = (title or "").lower()
    company_lower = (company or "").lower()

    # Always keep Qualtrics — never treat it as a competitor
    is_qualtrics = "qualtrics" in company_lower

    # Reject competitor companies
    if not is_qualtrics:
        if any(_matches(company_lower, c) for c in COMPETITOR_COMPANIES):
            return False

    # Reject blocklisted title patterns
    if any(_matches(title_lower, b) for b in TITLE_BLOCKLIST):
        return False

    # Must match at least one allowlist term in the title
    return any(_matches(title_lower, a) for a in TITLE_ALLOWLIST)


def categorize(title, description=""):
    """Return category tags for a job (used by the website filter buttons)."""
    text = (title + " " + (description or "")).lower()
    tags = []

    if any(_matches(text, t) for t in [
        "customer experience", "cx", "voice of customer", "voc",
        "customer feedback", "customer insights", "customer listening",
        "nps", "csat", "customer research",
    ]):
        tags.append("cx")

    if any(_matches(text, t) for t in [
        "employee experience", "employee listening", "employee insights",
        "people insights", "employee feedback", "workforce insights", "people analytics",
    ]):
        tags.append("ex")

    if any(_matches(text, t) for t in [
        "experience management", "xm", "qualtrics",
        "experience platform", "experience program",
    ]):
        tags.append("xm")

    if any(_matches(text, t) for t in [
        "insights", "analytics", "research", "survey", "nps", "csat",
    ]):
        tags.append("insights")

    if not tags:
        tags.append("other")

    return list(dict.fromkeys(tags))  # dedupe, preserve order
