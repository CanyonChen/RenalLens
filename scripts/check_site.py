"""Verify local dependencies of the six published entry pages."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "docs"
PAGES = ("index.html", "results/figures/cohort.html", "results/figures/scales.html",
         "reanalysis/missing_data.html", "reanalysis/index.html", "clinical_report.html", "presentation/deck.html")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("src", "href") and value:
                self.targets.append(value)


def check():
    failures = []
    checked = 0
    for name in PAGES:
        file = ROOT / name
        content = file.read_text(encoding="utf-8")
        for marker in ("__STUDY_DATA__", "__PAGE_SCRIPT__", "__PROJECT_NAV__", "__REPORT_CSS__"):
            if marker in content:
                failures.append(f"{name}: unresolved marker {marker}")
        links = Links()
        links.feed(content)
        for target in links.targets:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = (file.parent / unquote(parsed.path)).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.exists():
                failures.append(f"{name}: missing local target {target}")
            checked += 1
    if failures:
        raise AssertionError("\n".join(failures))
    print(f"Verified {checked} local links/assets across {len(PAGES)} published pages.")


if __name__ == "__main__":
    check()
