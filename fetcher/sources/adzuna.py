import hashlib
import os
import sys

import requests
from dateutil import parser as dateparser

_HERE = os.path.dirname(os.path.abspath(__file__))
_FETCHER = os.path.dirname(_HERE)
if _FETCHER not in sys.path:
    sys.path.insert(0, _FETCHER)
import job_filter

APP_ID = os.environ.get("ADZUNA_APP_ID", "")
API_KEY = os.environ.get("ADZUNA_API_KEY", "")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"

# XM practitioner role searches — focused on buyers/users of XM software
SEARCH_TERMS = [
    "customer experience manager",
    "customer experience director",
    "customer experience analyst",
    "customer experience lead",
    "employee experience manager",
    "employee experience director",
    "voice of customer manager",
    "voice of customer analyst",
    "VOC program manager",
    "customer insights manager",
    "customer insights director",
    "employee insights manager",
    "people insights manager",
    "customer listening",
    "employee listening",
    "NPS program manager",
    "NPS analyst",
    "CSAT manager",
    "experience program manager",
    "CX program manager",
    "experience management",
    "customer feedback manager",
    "employee feedback manager",
    "people analytics manager",
    "survey program manager",
    "Qualtrics",
]

COUNTRIES = ["us", "gb", "ca", "au"]


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

                    title = result.get("title", "")
                    company = result.get("company", {}).get("display_name", "Unknown")

                    if not job_filter.is_relevant(title, company):
                        continue

                    seen_urls.add(url)

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
                        "tags": job_filter.categorize(title, description),
                    })
            except Exception as e:
                print(f"  Adzuna error ({country} / {term!r}): {e}")

    return jobs
