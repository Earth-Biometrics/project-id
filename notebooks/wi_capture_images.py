#!/usr/bin/env python3
"""Download Wildlife Insights images through a logged-in Chrome (via remote debugging).

Each CSV "location" URL is a WI "Public Image" web page. When you are logged in,
that page calls WI's GraphQL API (with a short-lived Bearer token minted in the
page) to get a signed Google Cloud Storage URL, then shows the photo.

This script reuses your logged-in Chrome session efficiently:
  1. It loads ONE image page to capture the Bearer token.
  2. For every row it calls the same GraphQL query directly (no page render) to
     get the signed URL, then downloads the image bytes and saves a JPEG/PNG.
  3. If the token expires, it re-seeds automatically.

Prerequisite - start Chrome with remote debugging and log into WI once:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        --remote-debugging-port=9222 \
        --user-data-dir="$HOME/.wi_chrome_debug" \
        "https://app.wildlifeinsights.org"

Usage:
    python wi_capture_images.py --limit 20      # first 20 rows
    python wi_capture_images.py                 # all rows
    python wi_capture_images.py --overwrite     # re-download existing files
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# -- Configuration -----------------------------------------------------------
# Playwright owns the browser via a persistent profile so your WI login is
# remembered between runs. Log into WI once in the window it opens.
USER_DATA_DIR = str(Path.home() / ".wi_chrome_debug")
CDP_URL = "http://127.0.0.1:9222"  # only used by --attach mode
CSV_PATH = Path(
    "/Volumes/BigMacX/ebio/project-id/wildlife/metadata/"
    "bwindi_tier1_images/images_subset_bwindi.csv"
)
OUTPUT_DIR = Path("/Volumes/BigMacX/ebio/project-id/wildlife/pictures/bwindi_jpegs")

GQL_URL = "https://api.wildlifeinsights.org/graphql"
GQL_QUERY = (
    "query getDataFilePublicDownloadUrl($downloadId: Int!, $projectId: Int, "
    "$imageUUID: String!) {\n  getDataFilePublicDownloadUrl(downloadId: "
    "$downloadId, projectId: $projectId, imageUUID: $imageUUID) {\n    url\n    "
    "__typename\n  }\n}\n"
)
GQL_HEADERS_BASE = {
    "content-type": "application/json",
    "accept": "application/json",
    "origin": "https://app.wildlifeinsights.org",
    "referer": "https://app.wildlifeinsights.org/",
}

LOCATION_RE = re.compile(
    r"/download/(\d+)/project/(\d+)/data-files/([^/?#]+)", re.IGNORECASE
)
# Re-seed the token proactively every N successful resolves (0 = never).
TOKEN_REFRESH_EVERY = 400
REQUEST_TIMEOUT_MS = 30_000
DELAY = 0.0  # seconds between images
# ----------------------------------------------------------------------------


def sanitize(text: str) -> str:
    keep = "-_. "
    return "".join(c if (c.isalnum() or c in keep) else "_" for c in (text or "").strip())


def ext_for(url: str) -> str:
    path = (url or "").split("?")[0].lower()
    return ".png" if path.endswith(".png") else ".jpeg"


def parse_ids(location: str):
    m = LOCATION_RE.search(location or "")
    if not m:
        return None, None, None
    return int(m.group(1)), int(m.group(2)), m.group(3)


def seed_token(page, seed_url: str, settle_seconds: int = 20) -> str:
    """Navigate the page to an image URL and capture the bearer token it sends."""
    token = {"v": None}

    def grab(req):
        if req.url.startswith(GQL_URL):
            auth = req.headers.get("authorization")
            if auth:
                token["v"] = auth

    page.on("request", grab)
    try:
        page.goto(seed_url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
    except Exception:
        pass
    deadline = time.time() + settle_seconds
    while time.time() < deadline and not token["v"]:
        try:
            page.wait_for_timeout(300)
        except Exception:
            break
    try:
        page.remove_listener("request", grab)
    except Exception:
        pass
    return token["v"]


def wait_for_login(page, seed_url: str, poll_seconds: int = 300) -> str:
    """Block until the user has logged in and a bearer token can be captured."""
    token = seed_token(page, seed_url)
    if token:
        return token
    print("\n>>> Please LOG IN to Wildlife Insights in the Chrome window that just opened.")
    print(">>> Waiting for login (up to %d seconds)...\n" % poll_seconds, flush=True)
    deadline = time.time() + poll_seconds
    while time.time() < deadline:
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass
        token = seed_token(page, seed_url, settle_seconds=8)
        if token:
            print(">>> Login detected. Continuing.\n", flush=True)
            return token
    return None


def resolve_url(page, token, download_id, project_id, uuid):
    """Return (status, signed_url_or_None) from the GraphQL API."""
    payload = {
        "operationName": "getDataFilePublicDownloadUrl",
        "variables": {"downloadId": download_id, "imageUUID": uuid, "projectId": project_id},
        "query": GQL_QUERY,
    }
    headers = dict(GQL_HEADERS_BASE)
    headers["authorization"] = token
    resp = page.request.post(
        GQL_URL, data=json.dumps(payload), headers=headers, timeout=REQUEST_TIMEOUT_MS
    )
    if resp.status == 401:
        return 401, None
    try:
        data = resp.json()
    except Exception:
        return resp.status, None
    node = (data.get("data") or {}).get("getDataFilePublicDownloadUrl") or {}
    return resp.status, node.get("url")


def _launch(pw):
    """Launch a Playwright-owned Chrome using the persistent WI profile."""
    context = pw.chromium.launch_persistent_context(
        USER_DATA_DIR,
        channel="chrome",
        headless=False,
        accept_downloads=True,
        args=["--no-first-run", "--no-default-browser-check"],
    )
    page = context.pages[0] if context.pages else context.new_page()
    return context, page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(CSV_PATH))
    ap.add_argument("--out", default=str(OUTPUT_DIR))
    ap.add_argument("--limit", type=int, default=0, help="max rows to process (0 = all)")
    ap.add_argument("--start", type=int, default=0, help="0-based row offset to start at")
    ap.add_argument("--stride", type=int, default=1, help="process every Nth row (sampling)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--delay", type=float, default=DELAY)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.csv, newline="", encoding="utf-8-sig") as fh:
        all_rows = list(csv.DictReader(fh))

    work = all_rows[args.start :]
    if args.stride > 1:
        work = work[:: args.stride]
    if args.limit:
        work = work[: args.limit]
    total = len(work)

    with sync_playwright() as pw:
        try:
            context, page = _launch(pw)
        except Exception as exc:
            print(f"ERROR: could not launch Chrome with profile {USER_DATA_DIR}: {exc}")
            print("Close any Chrome using that profile and retry.")
            sys.exit(2)

        seed_url = next(
            (r.get("location", "").strip() for r in all_rows if (r.get("location") or "").strip()),
            "",
        )
        if not seed_url:
            print("ERROR: no location URLs found in CSV.")
            sys.exit(1)
        token = wait_for_login(page, seed_url)
        if not token:
            print("ERROR: still could not capture auth token after login window timed out.")
            context.close()
            sys.exit(1)
        print(f"Auth token captured. Processing {total} rows "
              f"(start={args.start}, stride={args.stride}).", flush=True)

        downloaded = skipped = missing_preview = failed = 0
        since_refresh = 0

        for i, row in enumerate(work, start=1):
            location = (row.get("location") or "").strip()
            species = sanitize(row.get("Species", ""))
            deployment = sanitize(row.get("Deployment ID", ""))
            stem = sanitize(Path(row.get("Filename", "")).stem)
            image_id = sanitize(row.get("Image ID", ""))

            download_id, project_id, uuid = parse_ids(location)
            if not uuid or not stem:
                skipped += 1
                continue

            dest = out_dir / f"{species}--{deployment}--{stem}--{image_id}.jpeg"
            if dest.exists() and dest.stat().st_size > 1000 and not args.overwrite:
                skipped += 1
                continue

            if TOKEN_REFRESH_EVERY and since_refresh >= TOKEN_REFRESH_EVERY:
                token = seed_token(page, seed_url) or token
                since_refresh = 0

            # Resolve + download with automatic reconnect on a closed target.
            for attempt in (1, 2):
                try:
                    status, url = resolve_url(page, token, download_id, project_id, uuid)
                    if status == 401:
                        token = seed_token(page, seed_url) or token
                        status, url = resolve_url(page, token, download_id, project_id, uuid)
                    since_refresh += 1
                    if not url:
                        failed += 1
                        print(f"[{i}/{total}] FAIL (no url) {species}/{stem}", flush=True)
                        url = None
                        break
                    dl = page.request.get(url, timeout=REQUEST_TIMEOUT_MS)
                    if dl.status != 200:
                        missing_preview += 1
                        print(f"[{i}/{total}] MISS (HTTP {dl.status}) {species}/{stem}", flush=True)
                        url = None
                        break
                    body = dl.body()
                    if not body or len(body) < 1000:
                        failed += 1
                        print(f"[{i}/{total}] FAIL (empty) {species}/{stem}", flush=True)
                        url = None
                        break
                    dest = dest.with_suffix(ext_for(url))
                    dest.write_bytes(body)
                    downloaded += 1
                    if i % 50 == 0 or i == total:
                        print(f"[{i}/{total}] OK   {dest.name} ({len(body):,} bytes)  "
                              f"[down={downloaded} miss={missing_preview} fail={failed} skip={skipped}]",
                              flush=True)
                    break
                except Exception as exc:
                    if attempt == 1:
                        print(f"[{i}/{total}] reconnecting after: {type(exc).__name__}", flush=True)
                        try:
                            context, page = _launch(pw)
                            token = seed_token(page, seed_url) or token
                        except Exception as exc2:
                            print(f"  reconnect failed: {exc2}", flush=True)
                            time.sleep(5)
                    else:
                        failed += 1
                        print(f"[{i}/{total}] FAIL (error) {species}/{stem}: {exc}", flush=True)

            if args.delay:
                time.sleep(args.delay)

        print("\n=== Summary ===")
        print(f"  Downloaded      : {downloaded}")
        print(f"  Skipped (exists): {skipped}")
        print(f"  Missing preview : {missing_preview}  (WI has no _500 object; 404)")
        print(f"  Failed          : {failed}")
        try:
            context.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
