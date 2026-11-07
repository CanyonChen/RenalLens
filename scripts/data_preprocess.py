"""Prepare the three descriptive CKD cohorts from the original UCI CSV."""

import argparse
from datetime import date
import hashlib
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd


DICTIONARY_URL = "https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/336/data.csv"
FEATURES = (
    "age", "bp", "sg", "al", "su", "rbc", "pc", "pcc", "ba", "bgr", "bu",
    "sc", "sod", "pot", "hemo", "pcv", "wbcc", "rbcc", "htn", "dm", "cad",
    "appet", "pe", "ane",
)
MEASURES = ("hemo", "sc", "bu", "bgr", "bp")
# UCI gives "gms" for hemoglobin and leaves the packed cell volume unit unspecified.
UNITS = {
    "age": "years", "bp": "mmHg", "bgr": "mg/dL", "bu": "mg/dL", "sc": "mg/dL",
    "sod": "mEq/L", "pot": "mEq/L", "hemo": "g (UCI)", "pcv": None,
    "wbcc": "cells/cumm", "rbcc": "millions/cmm",
}
CODED_LEVELS = {
    "sg": ("1.005", "1.010", "1.015", "1.020", "1.025"),
    "al": tuple("012345"),
    "su": tuple("012345"),
}
CATEGORIES = {
    **CODED_LEVELS,
    "rbc": ("normal", "abnormal"), "pc": ("normal", "abnormal"),
    "pcc": ("present", "notpresent"), "ba": ("present", "notpresent"),
    "htn": ("yes", "no"), "dm": ("yes", "no"), "cad": ("yes", "no"),
    "appet": ("good", "poor"), "pe": ("yes", "no"), "ane": ("yes", "no"),
    "class": ("ckd", "notckd"),
}
MISSING_MARKERS = ("", "?", "nan", "na", "n/a")
VIEWS = ("observed", "complete_case", "imputed", "missing_mask")


def clean_column(raw: pd.Series) -> tuple[pd.Series, dict]:
    name = raw.name
    stripped = raw.str.strip()
    tokens = stripped.mask(stripped.str.lower().isin(MISSING_MARKERS))
    if name in CODED_LEVELS:
        # UCI's CSV writes equivalent nominal codes with varying decimal precision.
        codes = {float(level): level for level in CODED_LEVELS[name]}
        clean = pd.to_numeric(tokens, errors="coerce").map(codes).astype("string")
    elif name in CATEGORIES:
        lower = tokens.str.lower()
        clean = lower.where(lower.isin(CATEGORIES[name]))
    else:
        numbers = pd.to_numeric(tokens, errors="coerce").astype("float64")
        clean = numbers.where(np.isfinite(numbers))

    invalid = tokens.notna() & clean.isna()
    if invalid.any():
        examples = raw[invalid].head(5).to_dict()
        expected = CATEGORIES.get(name, "finite numerical measurement")
        raise ValueError(f"{name}: expected {expected}; invalid tokens by row_id: {examples}")

    normalized = clean if name in CATEGORIES else tokens
    changed = normalized.notna() & raw.ne(normalized)
    audit = {
        "role": "diagnosis label" if name == "class" else "explanatory feature",
        "type": "categorical" if name in CATEGORIES else "numerical",
        "unit_as_documented": UNITS.get(name),
        "observed_n": int(clean.count()),
        "missing_n": int(clean.isna().sum()),
        "missing_tokens": raw[tokens.isna()].value_counts().to_dict(),
        "trimmed_n": int(raw.ne(stripped).sum()),
        "normalized_spellings": dict(zip(raw[changed], normalized[changed])),
    }
    if name in CATEGORIES:
        audit["allowed_levels"] = CATEGORIES[name]
    return clean, audit


def duplicate_summary(frame: pd.DataFrame) -> dict:
    return {
        "excess_copies": int(frame.duplicated().sum()),
        "row_ids_in_repeated_rows": frame.index[frame.duplicated(keep=False)].tolist(),
    }


def preprocess(source: Path, processed_dir: Path, download_date: date | None = None) -> None:
    contents = source.read_bytes()
    raw = pd.read_csv(BytesIO(contents), encoding="utf-8-sig", dtype="string", na_filter=False)
    columns = (*FEATURES, "class")
    missing = sorted(set(columns) - set(raw.columns))
    unexpected = sorted(set(raw.columns) - set(columns))
    if missing or unexpected:
        raise ValueError(f"Expected the UCI CSV schema; missing={missing}, unexpected={unexpected}")
    raw = raw.loc[:, list(columns)]
    raw.index = pd.RangeIndex(1, len(raw) + 1, name="row_id")
    observed = pd.DataFrame(index=raw.index)
    column_audits = {}
    for name in columns:
        observed[name], column_audits[name] = clean_column(raw[name])

    mask = observed.loc[:, list(FEATURES)].isna()
    complete_case = observed.loc[~mask.any(axis=1)]
    imputed = observed.copy()
    for name in FEATURES:
        values = observed[name].dropna()
        if values.empty:
            raise ValueError(f"{name}: no observed values from which to estimate a fill value")
        if name in CATEGORIES:
            modes = values.mode().sort_values()
            fill = str(modes.iloc[0])
            column_audits[name]["tied_modal_levels"] = modes.tolist() if len(modes) > 1 else []
        else:
            fill = float(values.median())
        imputed[name] = observed[name].fillna(fill)
        column_audits[name]["fill_value"] = fill

    audit = {
        "input_path": str(source.resolve()),
        "reference_csv_url": SOURCE_URL,
        "dictionary_url": DICTIONARY_URL,
        "input_sha256": hashlib.sha256(contents).hexdigest(),
        "download_date": download_date.isoformat() if download_date else None,
        "row_id": "One-based data record position in the original CSV, excluding the header.",
        "source_n": len(raw),
        "complete_case_n": len(complete_case),
        "imputed_n": len(imputed),
        "missing_markers_after_trim_and_lowercase": MISSING_MARKERS,
        "complete_case_rule": "All 24 explanatory features observed.",
        "imputation_rule": (
            "Column medians and categorical modes of all observed records, without diagnosis. "
            "Mode ties use the lexicographically first canonical code. Diagnosis is retained as supplied."
        ),
        "duplicate_rule": "Compare all 25 source fields, excluding row_id. Retain all records.",
        "duplicates_before_cleaning": duplicate_summary(raw),
        "duplicates_after_cleaning": duplicate_summary(observed),
        "columns": column_audits,
    }
    tables = {
        "observed": observed, "complete_case": complete_case,
        "imputed": imputed, "missing_mask": mask.astype("int8"),
    }
    names = [f"{name}.csv" for name in tables] + ["preprocessing_audit.json"]
    if any((processed_dir / name).resolve() == source.resolve() for name in names):
        raise ValueError("The output directory would overwrite the source CSV.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=processed_dir, prefix=".preprocess-") as tmp:
        staging = Path(tmp)
        for name, frame in tables.items():
            frame.to_csv(staging / f"{name}.csv", index_label="row_id")
        (staging / "preprocessing_audit.json").write_text(
            json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
        )
        for name in names:
            (staging / name).replace(processed_dir / name)


def load_view(processed_dir: Path, name: str) -> pd.DataFrame:
    """Read a saved view, preserving nominal codes and source row identifiers."""
    if name not in VIEWS:
        raise ValueError(f"Unknown view {name!r}; expected one of {VIEWS}")
    if name == "missing_mask":
        types = {feature: "int8" for feature in FEATURES}
    else:
        types = {feature: "string" for feature in CATEGORIES}
        types.update({feature: "float64" for feature in UNITS})
    types["row_id"] = "int64"
    return pd.read_csv(processed_dir / f"{name}.csv", dtype=types, index_col="row_id")


def patient_records(observed: pd.DataFrame, mask: pd.DataFrame) -> list[dict]:
    """Keep source identity and cell provenance when linking different charts."""
    records = []
    for row_id, group in observed["class"].fillna("unknown").items():
        missing = mask.loc[row_id].astype(bool)
        records.append({"id": int(row_id), "group": group, "missing": missing.index[missing].tolist()})
    return records


def _json_value(value):
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if pd.isna(value):
        return None
    return value.item() if isinstance(value, np.generic) else value


def write_report(name: str, payload: dict, output_dir: Path) -> None:
    templates = Path(__file__).with_name("views")
    page = (templates / f"{name}.html").read_text(encoding="utf-8")
    style = (templates / "report.css").read_text(encoding="utf-8")
    data = json.dumps(_json_value(payload), ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    # Keep JSON strings inside the embedded data block, including any literal </script> text.
    page = page.replace("__REPORT_CSS__", style).replace("__STUDY_DATA__", data.replace("<", "\\u003c"))
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    (figures / f"{name}.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw/ckd.csv"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--download-date", type=date.fromisoformat, metavar="YYYY-MM-DD")
    args = parser.parse_args()
    preprocess(args.input, args.processed_dir, args.download_date)


if __name__ == "__main__":
    main()
