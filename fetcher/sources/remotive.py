import hashlib
import re

import requests

RELEVANT_TERMS = [
    "experience management", "customer experience", "employee experience",
    "voice of customer", "voc ", " cx ", "cx manager", "cx analyst",
    " ex ", "ex manager", " xm ", "qualtrics", "medallia",
    "customer insights", "employee insights", "customer listening",
    "employee listening", "nps", "csat", "customer feedback",
]


def _is_relevant(title, description):
    text = (title + " " + (description or "")).lower()
    return any(t in text for t in RELEVANT_TERMS)


def _strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _categorize(title, description):
    text = (title + " " + (description or "")).lower()
    tags = []
    if any(t in text for t in ["customer experience", " cx ", "voice of customer",
                                "voc ", "customer feedback", "nps", "csat"]):
        tags.append("cx")
    if any(t in text for t in ["employee experience", " ex ", "employee listening",
                                "people insights", "employee feedback"]):
        tags.append("ex")
    if any(t in text for t in ["experience management", " xm ", "qualtrics", "medallia"]):
        tags.append("xm")
    if any(t in text for t in ["insights", "analytics", "research", "survey"]):
        tags.append("insights")
    if not tags:
        tags.append("other")
    return list(dict.fromkeys(tags))


def fetch():
    jobs = []
    seen_urls = set()

    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"limit": 500},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for result in data.get("jobs", []):
            title = result.get("title", "")
            description = _strip_html(result.get("description", ""))

            if not _is_relevant(title, description):
                continue

            url = result.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            posted_raw = result.get("publication_date", "")
            posted = posted_raw[:10] if posted_raw else ""
            job_id = hashlib.md5(url.encode()).hexdigest()[:12]

            jobs.append({
                "id": job_id,
                "title": title,
                "company": result.get("company_name", "Unknown"),
                "location": "Remote",
                "remote": True,
                "url": url,
                "posted": posted,
                "description": description[:500],
                "source": "remotive",
                "country": "Remote",
                "tags": _categorize(title, description),
            })
    except Exception as e:
        print(f"  Remotive error: {e}")

    return jobs
