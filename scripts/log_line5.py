#!/usr/bin/env python3
"""Append the TTC's next-train predictions for every Line 5 platform to a daily CSV.

Usage: log_line5.py OUTPUT_DIR
Used to study whether Line 5 delays can be detected from the predictions alone.
"""
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

NTAS = "https://ntas.ttc.ca/api/ntas/get-next-train-time/"
# Every Line 5 platform stop (Mount Dennis to Kennedy), from the TTC's GTFS stops list.
STOPS = [16067, *range(16069, 16081), *range(16082, 16087), *range(16202, 16232)]


def fetch(stop):
    req = Request(NTAS + str(stop), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except Exception:
        return None
    if not data or data[0].get("line") != "5":
        return None
    return stop, data[0].get("direction"), data[0].get("nextTrains", "")


def main(out_dir):
    now = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = [r for r in pool.map(fetch, STOPS) if r]
    day = now.astimezone(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d")
    path = Path(out_dir) / f"{day}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["utc_time", "stop_id", "direction", "next_trains_min"])
        for stop, direction, trains in rows:
            w.writerow([now.strftime("%Y-%m-%dT%H:%M:%SZ"), stop, direction, trains])
    print(f"logged {len(rows)} of {len(STOPS)} stops")


if __name__ == "__main__":
    main(sys.argv[1])
