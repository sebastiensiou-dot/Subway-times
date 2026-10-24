#!/usr/bin/env python3
"""Save current Line 1 / Line 5 alerts to alerts.json.

The TTC alerts feed doesn't allow browser requests from other sites (no CORS),
so a scheduled job fetches it and the page reads the saved copy instead.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

FEED = "https://alerts.ttc.ca/api/alerts/live-alerts"
OUT = Path(__file__).resolve().parent.parent / "alerts.json"
LINES = {"1", "5"}


def main():
    req = Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    alerts = []
    for r in data.get("routes", []):
        if r.get("routeType") != "Subway" or str(r.get("route")) not in LINES:
            continue
        period = r.get("activePeriod") or {}
        alerts.append({
            "route": str(r["route"]),
            "text": r.get("headerText") or r.get("title") or "Service alert",
            "type": r.get("alertType"),
            "severity": r.get("severity"),
            "updated": r.get("lastUpdated"),
            "start": period.get("start"),
            "end": period.get("end"),
        })
    alerts.sort(key=lambda a: (a["route"], a["start"] or ""))

    # Rounded to the hour so the file only changes (and commits) when alerts
    # change or once an hour, while still showing the page when the job stalls.
    checked = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    OUT.write_text(json.dumps({"checked": checked.isoformat(), "alerts": alerts}, indent=1) + "\n")


if __name__ == "__main__":
    main()
