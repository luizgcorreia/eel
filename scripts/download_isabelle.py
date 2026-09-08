#!/usr/bin/env python3
"""Fast parallel multi-part downloader for Isabelle."""

import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "https://mirror.clarkson.edu/isabelle/dist/Isabelle2025-2_linux.tar.gz"
DEST = os.path.expanduser("~/Isabelle2025-2_linux.tar.gz")
NUM_THREADS = 12
CHUNK_SIZE = 1024 * 1024  # 1MB buffer


def get_file_size(url: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return int(resp.headers.get("Content-Length", 0))


def download_chunk(url: str, dest_path: str, start: int, end: int, part_num: int):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={start}-{end}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest_path, "r+b") as f:
            f.seek(start)
            while True:
                buf = resp.read(CHUNK_SIZE)
                if not buf:
                    break
                f.write(buf)
    return part_num


def main():
    total_size = get_file_size(URL)
    if not total_size:
        print("Failed to get total file size.")
        sys.exit(1)

    print(f"Total size: {total_size / (1024*1024):.1f} MB across {NUM_THREADS} threads.")
    t0 = time.time()

    # Pre-allocate output file
    with open(DEST, "wb") as f:
        f.truncate(total_size)

    part_size = total_size // NUM_THREADS
    tasks = []

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for i in range(NUM_THREADS):
            start = i * part_size
            end = total_size - 1 if i == NUM_THREADS - 1 else (i + 1) * part_size - 1
            tasks.append(executor.submit(download_chunk, URL, DEST, start, end, i))

        completed = 0
        for future in as_completed(tasks):
            part = future.result()
            completed += 1
            elapsed = time.time() - t0
            pct = (completed / NUM_THREADS) * 100
            speed = ((completed * part_size) / (1024 * 1024)) / max(elapsed, 0.001)
            print(f"[{completed}/{NUM_THREADS}] Part {part} finished ({pct:.0f}%) - {speed:.1f} MB/s")

    elapsed = time.time() - t0
    avg_speed = (total_size / (1024 * 1024)) / elapsed
    print(f"Download completed in {elapsed:.1f}s ({avg_speed:.2f} MB/s) -> {DEST}")


if __name__ == "__main__":
    main()
