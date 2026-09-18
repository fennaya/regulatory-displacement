"""Stream-download the BACI zip with resume support, logging progress.

Downloads to a `.part` file and only renames to the final path after the
size and zip integrity both check out, so a killed/duplicated download can
never be mistaken for a complete, usable file. A lock file guards against
two instances writing to the same `.part` file concurrently.
"""

from __future__ import annotations

import sys
import time
import zipfile

import requests

from displacement_observatory.config import BACI_ZIP_PATH, BACI_ZIP_URL

CHUNK = 8 * 1024 * 1024
PART_PATH = BACI_ZIP_PATH.with_suffix(BACI_ZIP_PATH.suffix + ".part")
LOCK_PATH = BACI_ZIP_PATH.with_suffix(BACI_ZIP_PATH.suffix + ".lock")


def main() -> None:
    BACI_ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)

    if BACI_ZIP_PATH.exists():
        print(f"Already downloaded: {BACI_ZIP_PATH}")
        return

    try:
        lock_fd = open(LOCK_PATH, "x")
    except FileExistsError:
        print(
            f"ERROR: lock file {LOCK_PATH} already exists. Another download may be "
            "running, or a previous one was killed uncleanly -- check for stray "
            "python processes before deleting the lock and retrying.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        _download()
    finally:
        lock_fd.close()
        LOCK_PATH.unlink(missing_ok=True)


def _download() -> None:
    head = requests.head(BACI_ZIP_URL, timeout=30)
    total = int(head.headers.get("Content-Length", 0))
    accepts_ranges = head.headers.get("Accept-Ranges") == "bytes"

    existing = PART_PATH.stat().st_size if PART_PATH.exists() else 0
    headers = {}
    mode = "wb"
    if existing and total and existing < total and accepts_ranges:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"
        print(f"Resuming from byte {existing} of {total}.")
    elif existing:
        print(f"Discarding {existing} stale partial bytes (no resume support or already complete).")
        existing = 0

    start = time.time()
    downloaded = existing
    last_report = start
    with requests.get(BACI_ZIP_URL, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(PART_PATH, mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_report >= 5:
                    pct = (downloaded / total * 100) if total else 0.0
                    mb = downloaded / 1e6
                    mbps = (downloaded - existing) / 1e6 / max(now - start, 1e-6)
                    print(f"{mb:,.0f} MB / {total/1e6:,.0f} MB ({pct:.1f}%) @ {mbps:.1f} MB/s", flush=True)
                    last_report = now

    final_size = PART_PATH.stat().st_size
    if total and final_size != total:
        print(f"ERROR: size mismatch. Got {final_size:,} bytes, expected {total:,}.", file=sys.stderr)
        sys.exit(1)

    print("Verifying zip integrity...")
    with zipfile.ZipFile(PART_PATH) as zf:
        bad = zf.testzip()
    if bad is not None:
        print(f"ERROR: corrupt member in downloaded zip: {bad}", file=sys.stderr)
        sys.exit(1)

    PART_PATH.rename(BACI_ZIP_PATH)
    print(f"Done and verified. {BACI_ZIP_PATH} ({final_size:,} bytes).")


if __name__ == "__main__":
    main()
