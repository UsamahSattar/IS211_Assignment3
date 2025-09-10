# assignment3.py — Week 3 (robust CSV loader, regex, and a --peek debugger)

import argparse
import csv
import re
from collections import Counter
from datetime import datetime
from io import StringIO
from urllib.request import urlopen
import os

IMAGE_RE = re.compile(r"\.(jpg|gif|png)$", re.IGNORECASE)

def detect_browser(ua: str) -> str:
    ua = ua or ""
    if "Chrome" in ua and "Chromium" not in ua:
        return "Chrome"
    if "Firefox" in ua:
        return "Firefox"
    if "MSIE" in ua or "Trident" in ua:
        return "Internet Explorer"
    if "Safari" in ua and "Chrome" not in ua and "Chromium" not in ua:
        return "Safari"
    return "Other"

def load_text(src: str) -> str:
    """Load from http/https, file:///, or a plain local path."""
    s = src.strip()
    low = s.lower()
    if low.startswith(("http://", "https://", "file://")):
        with urlopen(s) as resp:
            return resp.read().decode("utf-8", errors="replace")
    with open(s, "rb") as f:  # plain local path
        return f.read().decode("utf-8", errors="replace")

def sniff_reader(csv_text: str):
    """csv.reader with auto delimiter detection; fallback to comma."""
    sample = csv_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        delim = dialect.delimiter
    except Exception:
        delim = ","
    return csv.reader(StringIO(csv_text), delimiter=delim)

# accept multiple datetime shapes; None if we can’t parse (still count the row)
DT_FORMATS = ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%y %H:%M:%S")
def try_parse_dt(s: str):
    s = (s or "").strip()
    for fmt in DT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def parse_rows(csv_text: str):
    """Yield (path, dt_or_none, ua). Do not drop a row if dt fails."""
    for row in sniff_reader(csv_text):
        if not row:
            continue
        path = (row[0] if len(row) > 0 else "").strip()
        if not path:
            continue
        dt = try_parse_dt(row[1] if len(row) > 1 else "")
        ua = (row[2] if len(row) > 2 else "").strip()
        yield path, dt, ua

def main():
    ap = argparse.ArgumentParser(description="Week 3: CSV + regex text processing")
    ap.add_argument("--url", required=True, help="CSV source (http/https, file:///, or local path)")
    ap.add_argument("--hours", action="store_true", help="(Extra) print hits per hour if timestamps parse")
    ap.add_argument("--peek", type=int, default=0, help="Print first N parsed rows for debugging")
    args = ap.parse_args()

    csv_text = load_text(args.url)
    rows = list(parse_rows(csv_text))

    if args.peek:
        for i, (p, d, u) in enumerate(rows[:args.peek], 1):
            short_ua = (u[:60] + "...") if len(u) > 60 else u
            print(f"[{i}] path={p!r} dt={d} ua={short_ua!r}")

    total_requests = 0
    image_requests = 0
    browser_counts = Counter()
    hour_counts = Counter()

    for path, dt, ua in rows:
        total_requests += 1
        if IMAGE_RE.search(path):
            image_requests += 1
        browser_counts[detect_browser(ua)] += 1
        if dt:
            hour_counts[dt.hour] += 1

    if total_requests == 0:
        print("No requests found.")
        return

    pct = (image_requests / total_requests) * 100.0
    print(f"Image requests account for {pct:.1f}% of all requests")

    focus = {k: v for k, v in browser_counts.items()
             if k in {"Firefox", "Chrome", "Internet Explorer", "Safari"}}
    if focus:
        most, _ = max(focus.items(), key=lambda kv: kv[1])
        print(f"The most popular browser is {most}")
    else:
        print("No recognized browsers found.")

    if args.hours:
        if hour_counts:
            for hr, count in sorted(hour_counts.items(), key=lambda kv: kv[1], reverse=True):
                print(f"Hour {hr:02d} has {count} hits")
        else:
            print("Note: timestamps didn’t match known formats; no per-hour stats.")

if __name__ == "__main__":
    main()
