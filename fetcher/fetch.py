import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import adzuna, remotive, remoteok

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
JOBS_FILE = os.path.join(DOCS_DIR, "jobs.json")
MAX_AGE_DAYS = 30


def load_existing():
    try:
        with open(JOBS_FILE) as f:
            data = json.load(f)
            return {job["id"]: job for job in data.get("jobs", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def is_fresh(posted_date):
    if not posted_date:
        return True
    try:
        posted = datetime.strptime(posted_date, "%Y-%m-%d")
        return (datetime.utcnow() - posted).days <= MAX_AGE_DAYS
    except Exception:
        return True


def main():
    print("Loading existing jobs...")
    existing = load_existing()
    print(f"  {len(existing)} existing jobs on file")

    print("\nFetching from Adzuna...")
    adzuna_jobs = adzuna.fetch()
    print(f"  {len(adzuna_jobs)} jobs")

    print("\nFetching from Remotive...")
    remotive_jobs = remotive.fetch()
    print(f"  {len(remotive_jobs)} jobs")

    print("\nFetching from RemoteOK...")
    remoteok_jobs = remoteok.fetch()
    print(f"  {len(remoteok_jobs)} jobs")

    merged = dict(existing)
    for job in adzuna_jobs + remotive_jobs + remoteok_jobs:
        merged[job["id"]] = job

    fresh = {jid: job for jid, job in merged.items() if is_fresh(job.get("posted", ""))}

    jobs_list = sorted(fresh.values(), key=lambda j: j.get("posted", ""), reverse=True)

    output = {
        "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(jobs_list),
        "jobs": jobs_list,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. {len(jobs_list)} total jobs saved.")


if __name__ == "__main__":
    main()
