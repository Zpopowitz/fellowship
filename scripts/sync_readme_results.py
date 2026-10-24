"""Sync the results section of README.md from results/results.md.

Replaces everything between the RESULTS markers in README.md with the body of
results/results.md. Used by the .kiro/hooks/on_results_change.json hook.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
RESULTS_MD = os.path.join(ROOT, "results", "results.md")

BEGIN = "<!-- RESULTS:BEGIN -->"
END = "<!-- RESULTS:END -->"


def main():
    body = open(RESULTS_MD, encoding="utf-8").read().strip()
    # strip the leading "# Fellowship — Results" H1 so it nests under README's H2
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body = "\n".join(lines).strip()

    text = open(README, encoding="utf-8").read()
    if BEGIN in text and END in text:
        pre = text.split(BEGIN)[0]
        post = text.split(END)[1]
        text = f"{pre}{BEGIN}\n{body}\n{END}{post}"
    else:
        text += f"\n\n{BEGIN}\n{body}\n{END}\n"
    open(README, "w", encoding="utf-8").write(text)
    print("README results section synced from results/results.md")


if __name__ == "__main__":
    main()
