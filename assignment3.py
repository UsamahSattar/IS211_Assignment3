import argparse
import csv
import re
from collections import Counter
from datetime import datetime
from io import StringIO
from urllib.request import urlopen

IMAGE_RE = re.compile(r"\.(jpg|gif|png)$", re.IGNORECASE)

def detect_browser(user_agent: str) -> str:
    ua = user_agent or ""
    if "Chrome" in ua and "Chromium" not in ua:
        return "Chrome"
    if "Firefox" in ua:
        return "Firefox"
    if "MSIE" in ua or "Trident" in ua:
        return "Internet Explorer"
    if "Safari" in ua and "Chrome" not in ua and "Chromium" not in ua:
        return "Safari"
    return "Other"

def download_csv_text(url: str) -> str:
    with urlopen(url) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="replace")

def parse_rows(csv_text: str):
    reader = csv.reader(StringIO(csv_text))
    for row in reader:
        if not row or len(row) < 5:
            continue
        path = row[0].strip()
        dt_str = row[1].strip()
        ua = row[2].strip()
        try:
            dt = datetime.strptime(dt_str, "%m/%d/%Y %H:%M:%S")
        except ValueError:
            continue
        yield path, dt, ua

def main():
    ap = argparse.ArgumentParser(description="Week 3: CSV + regex text processing")
    ap.add_argument("--url", required=True, help="URL of the weblog CSV")
    ap.add_argument("--hours", action="store_true",
                    help="(Extra credit) print hours sorted by number of hits")
    args = ap.parse_args()

    csv_text = download_csv_text(args.url)

    total_requests = 0
    image_requests = 0
    browser_counts = Counter()
    hour_counts = Counter()

    for path, dt, ua in parse_rows(csv_text):
        total_requests += 1
        if IMAGE_RE.search(path):
            image_requests += 1
        browser_counts[detect_browser(ua)] += 1
        hour_counts[dt.hour] += 1

    if total_requests == 0:
        print("No requests found.")
        return

    percent_images = (image_requests / total_requests) * 100.0
    print(f"Image requests account for {percent_images:.1f}% of all requests")

    focus = {k: v for k, v in browser_counts.items()
             if k in {"Firefox", "Chrome", "Internet Explorer", "Safari"}}
    if focus:
        most_popular, _ = max(focus.items(), key=lambda kv: kv[1])
        print(f"The most popular browser is {most_popular}")
    else:
        print("No recognized browsers found.")

    if args.hours:
        for hr, count in sorted(hour_counts.items(), key=lambda kv: kv[1], reverse=True):
            print(f"Hour {hr:02d} has {count} hits")

if __name__ == "__main__":
    main()
