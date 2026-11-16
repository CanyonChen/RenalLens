"""Rebuild the published RenalLens analysis and offline site on any platform."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "0eeea8d17f5ad8792d854999d6ddf1602ec4e116616f6ccdfdaef0ba8109e694"


def run(script, *args):
    command = [sys.executable, str(ROOT / script), *map(str, args)]
    print("RUN", script, *args, flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download the checksum-verified official UCI input if missing")
    parser.add_argument("--pdf", action="store_true", help="Render the slides with Chrome and compile the poster/report with Tectonic or latexmk")
    parser.add_argument("--check", action="store_true", help="Run numerical and real-browser checks; requires npm ci and Chrome/Playwright")
    parser.add_argument("--package", action="store_true", help="Write outputs/RenalLens-offline.zip containing the published site")
    args = parser.parse_args()
    source = ROOT / "data/raw/ckd.csv"
    if not source.exists() and args.download:
        source.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen("https://archive.ics.uci.edu/static/public/336/data.csv", timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise ValueError("UCI input checksum changed; review the new source before rebuilding the authored narrative.")
        source.write_bytes(data)
    if not source.exists():
        parser.error("Missing data/raw/ckd.csv; run again with --download.")
    if hashlib.sha256(source.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Input checksum differs from the UCI data interpreted by the published narrative.")
    run("scripts/data_preprocess.py")
    run("scripts/test.py", "--output-dir", "docs/results", "--plots")
    run("scripts/train.py", "--output-dir", "docs/results", "--plots")
    run("scripts/eligibility.py")
    run("scripts/statistical_reanalysis.py")
    run("scripts/reanalysis_diagnostics.py")
    run("scripts/missing_data_sensitivity.py")
    run("scripts/reanalysis_figures.py")
    run("scripts/clinical_questions.py")
    run("scripts/clinical_question_figures.py")
    run("scripts/clinical_figures.py", "--output-dir", "docs/results", "--report", "docs/clinical_report.html")
    run("scripts/build_site.py")
    run("scripts/build_presentation.py", *(["--render"] if args.pdf else []))
    for folder in ("poster", "report"):
        run(f"docs/{folder}/{folder}_figures.py")
    if args.pdf:
        tectonic = shutil.which("tectonic")
        local = ROOT / ".tools/tectonic/tectonic.exe"
        if not tectonic and local.exists():
            tectonic = str(local)
        latexmk = shutil.which("latexmk")
        if not tectonic and not latexmk:
            parser.error("PDF compilation needs Tectonic or latexmk; see docs/poster/BUILD.md.")
        env = os.environ.copy()
        cache = ROOT / ".tools/tectonic-cache"
        cache.mkdir(parents=True, exist_ok=True)
        env.update(TECTONIC_CACHE_DIR=str(cache), TEMP=str(cache), TMP=str(cache))
        fontconfig = ROOT / ".tools/fonts.conf"
        if fontconfig.exists():
            env["FONTCONFIG_FILE"] = str(fontconfig)
        for folder, job in (("poster", "RenalLens_Poster"), ("report", "RenalLens_Report")):
            target = ROOT / "docs" / folder
            if tectonic:
                subprocess.run([tectonic, "main.tex", "--outdir", str(target)], cwd=target, check=True, env=env)
                shutil.copyfile(target / "main.pdf", target / f"{job}.pdf")
                (target / "main.pdf").unlink()
            else:
                subprocess.run([latexmk, "-xelatex", "-interaction=nonstopmode", f"-jobname={job}", "main.tex"], cwd=target, check=True)
    if args.check:
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT, check=True)
        npm = shutil.which("npm")
        if not npm:
            parser.error("Browser checks need Node.js and npm ci.")
        subprocess.run([npm, "test"], cwd=ROOT, check=True)
        subprocess.run([npm, "run", "check:browser"], cwd=ROOT, check=True)
        run("scripts/check_site.py")
    if args.package:
        target = ROOT / "outputs/RenalLens-offline.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in sorted((ROOT / "docs").rglob("*")):
                if file.is_file() and file.suffix.lower() in {".html", ".css", ".js", ".svg", ".png", ".jpg", ".pdf", ".csv", ".json", ".md", ".woff", ".woff2"} and not any("template" in part for part in file.parts):
                    archive.write(file, file.relative_to(ROOT / "docs"))
        print("Offline package:", target)


if __name__ == "__main__":
    main()
