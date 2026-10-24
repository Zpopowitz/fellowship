"""Re-download the raw Boston SAR source files, verifying each by sha256.

The raw ~575 MB of source data is NOT committed to the repo (judges should not
have to clone it, and `data/processed/` already holds everything the gym needs).
This script re-fetches every file listed in scripts/boston_data_manifest.json
into boston_data/<folder>/<file> using the DEFAULT User-Agent, and checks each
file's sha256 against the manifest.

Run:  python scripts/download_boston_data.py
      python scripts/download_boston_data.py --only D13_fire_incidents

Provenance (URLs, sizes, hashes, licenses) is documented in docs/DATA_SOURCES.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFEST = os.path.join(HERE, "boston_data_manifest.json")
DEST = os.path.join(ROOT, "boston_data")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="download only entries whose folder contains this substring")
    args = ap.parse_args()

    entries = json.load(open(MANIFEST, encoding="utf-8"))
    if args.only:
        entries = [e for e in entries if args.only in e["folder"]]
    if not entries:
        print("no manifest entries match", file=sys.stderr)
        return 1

    ok = bad = 0
    for e in entries:
        out_dir = os.path.join(DEST, e["folder"])
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, e["file"])
        if os.path.exists(out) and sha256(out) == e["sha256"]:
            print(f"  have   {e['folder']}/{e['file']}")
            ok += 1
            continue
        print(f"  get    {e['folder']}/{e['file']} ...", flush=True)
        try:
            # default User-Agent on purpose (no spoofing).
            urllib.request.urlretrieve(e["url"], out)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL   download error: {exc}", file=sys.stderr)
            bad += 1
            continue
        got = sha256(out)
        if got == e["sha256"]:
            print(f"  ok     sha256 verified")
            ok += 1
        else:
            print(f"  FAIL   sha256 mismatch: expected {e['sha256'][:12]} got {got[:12]}",
                  file=sys.stderr)
            bad += 1
    print(f"\n{ok} ok, {bad} failed, into {DEST}")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
