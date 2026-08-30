#!/usr/bin/env python3

import os
import csv
import time
from concurrent.futures import ThreadPoolExecutor
import requests

# --- CONFIGURATION ---
CSV_FILE_PATH = "images.csv"          # Path to your Wildlife Insights CSV
OUTPUT_FOLDER = "downloaded_images"    # Where to save the gorilla photos
MAX_WORKERS = 10                       # Number of concurrent downloads

# Paste your exact browser cookie string here
SESSION_COOKIE = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IndpbGRsaWZlLWluc2lnaHRzIn0.eyJkYXRhIjp7InVzZXJFbWFpbCI6IkxlbyIsImlkIjoyMDM0NTQwLCJyb2xlIjoiUFVCTElDIn0sImlhdCI6MTc4Nzk1MDM3OCwiZXhwIjoxNzg4MDM2Nzc4LCJhdWQiOiJ3aWxkbGlmZS1pbnNpZ2h0cyIsImlzcyI6IndpbGRsaWZlLWluc2lnaHRzIn0.GIfL6QjUmVuCpk1mf6LVQWSzvE10W0dPiwwaYHE9PRmEV84tpb1JltMBXjH7xi0WVEhpO1VURVlQH1m25n58Vv7xzPLQF3L77h-xiyVxdbnUsypm_NhentdUEZteL_rc8SEplq5a1MWehkV_LVfucAtJNpSHcxzCTYZLAPsMaCkD-B9Ssfk2rxSS-6p_Jn3PrvKMO6zO_ST4G493MObv7L3GlCQ2s0ucV7JE9i-564JYdZTZyde-w2mYmzuqJmmxAWZ58vrhz76LVq-uNdnenabCyjxdusMlxDPac02GosJiQfZGiqAR_I-AdRM23Q3ckcxLoQb-9XrGQxPSQCBVkA"

# Setup headers to look like your browser session
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": SESSION_COOKIE,
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
}

def download_image(row):
    """Worker function to download an individual image row."""
    # Wildlife Insights stores the secure link in the 'location' column
    url = row.get("location")
    image_id = row.get("image_id") or row.get("id")
    
    if not url or not image_id:
        return f"Skipped row: Missing URL or ID"
    
    # Establish a clean file name
    file_extension = ".jpg" # Default fallback
    file_path = os.path.join(OUTPUT_FOLDER, f"{image_id}{file_extension}")
    
    # Skip downloading if file already exists (allows resuming broken downloads)
    if os.path.exists(file_path):
        return f"Exists: {image_id}"
        
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return f"Success: {image_id}"
        else:
            return f"Failed: {image_id} (HTTP {response.status_code})"
    except Exception as e:
        return f"Error: {image_id} ({str(e)})"

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Load rows from CSV
    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Loaded {len(rows)} records. Starting multi-threaded download...")
    start_time = time.time()
    
    # Execute downloads concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(download_image, rows)
        
        # Print progress tracking
        for count, result in enumerate(results, 1):
            if count % 50 == 0 or "Failed" in result or "Error" in result:
                print(f"[{count}/{len(rows)}] {result}")
                
    end_time = time.time()
    print(f"Task complete in {round(end_time - start_time, 2)} seconds.")

if __name__ == "__main__":
    main()
