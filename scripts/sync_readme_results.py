"""Sync README.md result sections from generated results files.

Replaces the content between marker pairs in README.md with the body of the
matching results file:
  <!-- RESULTS:BEGIN --> ... <!-- RESULTS:END -->  <- results/results.md
  <!-- HAZARDS:BEGIN --> ... <!-- HAZARDS:END -->  <- results/hazards.md

Used by the README-sync hook. Every number in these sections therefore comes
from a file a script generated, never hand-typed.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")

SECTIONS = [
    ("RESULTS", os.path.join(ROOT, "results", "results.md")),
    ("HAZARDS", os.path.join(ROOT, "results", "hazards.md")),
]


def _body(path):
    body = open(path, encoding="utf-8").read().strip()
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):  # drop the H1 so it nests under README's H2
        lines = lines[1:]
    return "\n".join(lines).strip()


def main():
    text = open(README, encoding="utf-8").read()
    synced = []
    for name, path in SECTIONS:
        if not os.path.exists(path):
            continue
        begin, end = f"<!-- {name}:BEGIN -->", f"<!-- {name}:END -->"
        body = _body(path)
        if begin in text and end in text:
            pre = text.split(begin)[0]
            post = text.split(end)[1]
            text = f"{pre}{begin}\n{body}\n{end}{post}"
            synced.append(name)
        else:
            text += f"\n\n{begin}\n{body}\n{end}\n"
            synced.append(name + " (appended)")
    open(README, "w", encoding="utf-8").write(text)
    print("README synced:", ", ".join(synced) if synced else "nothing (no results files)")


if __name__ == "__main__":
    main()
