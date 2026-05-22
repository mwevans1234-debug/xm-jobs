import hashlib
import os

import requests
from dateutil import parser as dateparser

APP_ID = os.environ.get("ADZUNA_APP_ID", "")
API_KEY = os.environ.get("ADZUNA_API_KEY", "")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

SEARCH_TERMS = [
    "experience management",
    "customer experience manager",
    "customer experience director",
    "employee experience manager",
    "voice of customer",
    "VOC analyst",
    "customer insights manager",
    "employee insights",
    "customer listening",
    "employee listening",
    "CX program manager",
    "EX program manager",
    "customer feedback manager",
    "Qualtrics",
    "Medallia",
    "NPS analyst",
    "experience data analyst",
]

COUNTRIES = ["us", "gb", "ca", "au"]


def _categorize(title, description):
    text = (title + " " + (description or "")).lower()
    tags = []
    if any(t in text for t in ["customer experience", " cx ", "cx manager", "cx analyst",
                                "voice of customer", "voc ", "customer feedback",
                                "nps", "csat", "customer listening"]):
        tags.append("cx")
    if any(t in text for t in ["employee experience", " ex ", "employee listening",
                                "people insights", "employee engagement",
                                "employee insights", "employee feedback"]):
        tags.append("ex")
    if any(t in text for t in ["experience management", " xm ", "qualtrics", "medallia",
                                "experience platform", "experience program"]):
        tags.append("xm")
    if any(t in text for t in ["insights", "analytics", "data analyst",
                                "research", "nps", "csat", "survey"]):
        tags.append("insights")
    if not tags:
        tags.append("other")
    return list(dict.fromkeys(tags))


def fetch():
    if not APP_ID or not API_KEY:
        print("  Adzuna credentials not found — set ADZUNA_APP_ID and ADZUNA_API_KEY")
        return []

    jobs = []
    seen_urls = set()

    for country in COUNTRIES:
        for term in SEARCH_TERMS:
            try:
                resp = requests.get(
                    BASE_URL.format(country=country),
                    params={
                        "app_id": APP_ID,
                        "app_key": API_KEY,
                        "what": term,
                        "results_per_page": 50,
                        "sort_by": "date",
                        "max_days_old": 30,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                for result in data.get("results", []):
                    url = result.get("redirect_url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = result.get("title", "")
                    company = result.get("company", {}).get("display_name", "Unknown")
                    location = result.get("location", {}).get("display_name", "")
                    description = result.get("description", "")
                    created = result.get("created", "")

                    try:
                        posted = dateparser.parse(created).strftime("%Y-%m-%d") if created else ""
                    except Exception:
                        posted = ""

                    job_id = hashlib.md5(url.encode()).hexdigest()[:12]
                    is_remote = "remote" in location.lower() or "remote" in title.lower()

                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "remote": is_remote,
                        "url": url,
                        "posted": posted,
                        "description": description[:500],
                        "source": "adzuna",
                        "country": country.upper(),
                        "tags": _categorize(title, description),
                    })
            except Exception as e:
                print(f"  Adzuna error ({country} / {term!r}): {e}")

    return jobs
