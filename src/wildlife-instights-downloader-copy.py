#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import pandas as pd
import requests

# ---------------- CONFIGURATION ---------------- #
CSV_FILE = "images.csv"
OUTPUT_DIR = "/Users/elhorte/git/ebio/project-id/downloaded_images"
MAX_WORKERS = 8  # Number of concurrent downloads

# Your extracted Bearer Token
AUTH_TOKEN = (
    "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IndpbGRsaWZlLWluc2lnaHRzIn0."
    "eyJkYXRhIjp7InVzZXJFbWFpbCI6IkxlbyIsImlkIjoyMDM0NTQwLCJyb2xlIjoiUFVCTElDIn0sImlh"
    "dCI6MTc4ODA0MDQxNSwiZXhwIjoxNzg4MTI2ODE1LCJhdWQiOiJ3aWxkbGlmZS1pbnNpZ2h0cyIsImlz"
    "cyI6IndpbGRsaWZlLWluc2lnaHRzIn0.LfL81nHOohZPQYRhWeROZD1ta4nmeSbM7Jd_1xUWlx3AFIRs"
    "EVhHjWeWDI2YJwGJDBhzx9AHjy8N4jGljregW3dDaN5qjwoV_KXmLdznOxorrzDTqhKi28aEdTRH60QF"
    "PKdtxczVt5NhFjqdSZS21-lJYdihNJtCMw1Lxula5xQU6_WBL30vTut8BVuLlqcU6fDiLdSrdZ5CFb9Z"
    "OQu7Y8i4H7S-1KU8jOzxzclhf6XFGc5bOsXjLXdd-iemMbEkzoBLDCG6otnLmVFSSagVLukONRBGJIjh"
    "MQXaoYVzu1fQ1WloR3lNukwvxN2at_AOmcqoiOY6w0r5VQ1YfwVXrw"
)

HEADERS = {
    "Authorization": AUTH_TOKEN,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}
# ----------------------------------------------- #

os.makedirs(OUTPUT_DIR, exist_ok=True)
df = pd.read_csv(CSV_FILE)


def download_image(row):
  url = row["location"]
  # Naming: <deployment_id>_<filename> (e.g. d7bfea19-3f88-41a8-a75c-2512a1bfcb15_IMG_1557.JPG)
  filename = f"{row['deployment_id']}_{row['filename']}"
  save_path = os.path.join(OUTPUT_DIR, filename)

  # Skip if already successfully downloaded (and is larger than a standard error payload, > 5KB)
  if os.path.exists(save_path) and os.path.getsize(save_path) > 5120:
    return f"Skipped (already exists): {filename}"

  try:
    response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
    response.raise_for_status()

    # Verify content type or inspect first chunk to avoid saving HTML error pages
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type or "application/json" in content_type:
      return f"Failed (Auth/Token expired or invalid format): {filename}"

    with open(save_path, "wb") as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    return f"Downloaded: {filename}"
  except Exception as e:
    return f"Error on {filename}: {e}"


# Run concurrent downloads
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
  futures = [executor.submit(download_image, row) for _, row in df.iterrows()]
  for future in as_completed(futures):
    print(future.result())
