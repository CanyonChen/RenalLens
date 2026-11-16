"""Repeated site builds must preserve bytes and keep a single navigation block."""
import shutil
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site


class SiteBuildTests(unittest.TestCase):
    def test_repeated_build_is_idempotent(self):
        with TemporaryDirectory() as directory:
            docs = Path(directory)
            (docs / "reanalysis/tables").mkdir(parents=True)
            shutil.copyfile(ROOT / "docs/reanalysis/tables/eligibility_rules.csv",
                            docs / "reanalysis/tables/eligibility_rules.csv")
            for relative in ("reanalysis/index.html", "reanalysis/missing_data.html", "clinical_report.html"):
                (docs / relative).write_text('<html><body><main><header>Study</header>\n<section id="selection">Results</section></main></body></html>', encoding="utf-8")
            with patch.object(build_site, "DOCS", docs):
                build_site.build()
                first = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*.html")}
                build_site.build()
                second = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*.html")}
            self.assertEqual(first, second)
            for relative in ("reanalysis/index.html", "reanalysis/missing_data.html", "clinical_report.html"):
                self.assertEqual((docs / relative).read_text(encoding="utf-8").count('aria-label="项目导航"'), 1)


if __name__ == "__main__":
    unittest.main()
