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
            "https://remoteok.com/api",
            headers={"User-Agent": "XMJobsAggregator/1.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for result in data:
            if not isinstance(result, dict) or "position" not in result:
                continue

            title = result.get("position", "")
            company = result.get("company", "Unknown")

            if not job_filter.is_relevant(title, company):
                continue

            url = result.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            description = _strip_html(result.get("description", ""))
            date_str = result.get("date", "")
            posted = date_str[:10] if date_str else ""
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
                "source": "remoteok",
                "country": "Remote",
                "tags": job_filter.categorize(title, description),
            })
    except Exception as e:
        print(f"  RemoteOK error: {e}")

    return jobs
