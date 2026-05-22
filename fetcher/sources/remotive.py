import hashlib
import os
import re
import sys

import requests

_HERE = os.path.dirname(os.path.abspath(__file__))
_FETCHER = os.path.dirname(_HERE)
if _FETCHER not in sys.path:
    sys.path.insert(0, _FETCHER)
import job_filter


def _strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()


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
            company = result.get("company_name", "Unknown")

            if not job_filter.is_relevant(title, company):
                continue

            url = result.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            description = _strip_html(result.get("description", ""))
            posted_raw = result.get("publication_date", "")
            posted = posted_raw[:10] if posted_raw else ""
            job_id = hashlib.md5(url.encode()).hexdigest()[:12]

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": "Remote",
                "remote": True,
                "url": url,
                "posted": posted,
                "description": description[:500],
                "source": "remotive",
                "country": "Remote",
                "tags": job_filter.categorize(title, description),
            })
    except Exception as e:
        print(f"  Remotive error: {e}")

    return jobs
