import hashlib
import os
import re
import sys
import time
from datetime import datetime

import feedparser

# Ensure fetcher/ is in path so job_filter can be imported
_HERE = os.path.dirname(os.path.abspath(__file__))
_FETCHER = os.path.dirname(_HERE)
if _FETCHER not in sys.path:
    sys.path.insert(0, _FETCHER)
import job_filter

# Exact-phrase searches — quotes force Indeed to match the full phrase in title/description
SEARCH_TERMS = [
    '"customer experience manager"',
    '"customer experience director"',
    '"customer experience analyst"',
    '"customer experience lead"',
    '"employee experience manager"',
    '"employee experience director"',
    '"voice of customer"',
    '"customer insights manager"',
    '"customer insights director"',
    '"employee insights manager"',
    '"people insights"',
    '"customer listening"',
    '"employee listening"',
    '"NPS analyst"',
    '"NPS manager"',
    '"experience management"',
    '"CX program manager"',
    '"experience program manager"',
    '"customer feedback manager"',
    '"people analytics manager"',
    '"CSAT manager"',
    '"survey program manager"',
]

COUNTRY_DOMAINS = [
    ("www.indeed.com", "US"),
    ("uk.indeed.com",  "UK"),
    ("ca.indeed.com",  "CA"),
    ("au.indeed.com",  "AU"),
]


def _parse_title_field(raw):
    """Split Indeed's 'Job Title - Company (City, ST)' format."""
    parts = raw.split(" - ", 1)
    title = parts[0].strip()
    company, location = "Unknown", ""
    if len(parts) > 1:
        rest = parts[1].strip()
        loc_match = re.search(r"\(([^)]+)\)\s*$", rest)
        if loc_match:
            location = loc_match.group(1)
            company = rest[: loc_match.start()].strip().rstrip(",").strip()
        else:
            company = rest
    return title, company, location


def fetch():
    jobs = []
    seen_urls = set()

    for domain, country_code in COUNTRY_DOMAINS:
        for term in SEARCH_TERMS:
            url = (
                f"https://{domain}/rss"
                f"?q={term.replace(' ', '+')}"
                f"&sort=date&fromage=30"
            )
            try:
                feed = feedparser.parse(
                    url,
                    request_headers={"User-Agent": "XMJobsAggregator/1.0"},
                )
                for entry in feed.entries:
                    raw_title = entry.get("title", "")
                    link = entry.get("link", "")

                    if not link or link in seen_urls:
                        continue

                    title, company, location = _parse_title_field(raw_title)

                    if not job_filter.is_relevant(title, company):
                        continue

                    seen_urls.add(link)

                    published = entry.get("published_parsed")
                    if published:
                        posted = datetime(*published[:6]).strftime("%Y-%m-%d")
                    else:
                        posted = ""

                    description = re.sub(
                        r"<[^>]+>", " ", entry.get("summary", "")
                    ).strip()

                    job_id = hashlib.md5(link.encode()).hexdigest()[:12]
                    is_remote = (
                        "remote" in location.lower() or "remote" in title.lower()
                    )

                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "remote": is_remote,
                        "url": link,
                        "posted": posted,
                        "description": description[:500],
                        "source": "indeed",
                        "country": country_code,
                        "tags": job_filter.categorize(title, description),
                    })

                time.sleep(1)  # be polite to Indeed's servers

            except Exception as e:
                print(f"  Indeed error ({domain} / {term}): {e}")

    return jobs
