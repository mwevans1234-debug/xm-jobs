import hashlib
import re

import requests

RELEVANT_TERMS = [
    "experience", "cx", "ex", "customer", "insights",
    "qualtrics", "medallia", "voc", "nps", "feedback", "listening",
]


def _is_relevant(title, tags_list):
    text = (title + " " + " ".join(tags_list or [])).lower()
    return any(t in text for t in RELEVANT_TERMS)


def _strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _categorize(title, description):
    text = (title + " " + (description or "")).lower()
    tags = []
    if any(t in text for t in ["customer experience", " cx ", "voice of customer",
                                "voc ", "customer feedback", "nps", "csat"]):
        tags.append("cx")
    if any(t in text for t in ["employee experience", " ex ", "employee listening"]):
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
            raw_tags = result.get("tags", [])

            if not _is_relevant(title, raw_tags):
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
                "company": result.get("company", "Unknown"),
                "location": "Remote",
                "remote": True,
                "url": url,
                "posted": posted,
                "description": description[:500],
                "source": "remoteok",
                "country": "Remote",
                "tags": _categorize(title, description),
            })
    except Exception as e:
        print(f"  RemoteOK error: {e}")

    return jobs
