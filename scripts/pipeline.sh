#!/usr/bin/env bash
set -eo pipefail

usage() {
    cat <<'EOF'
Usage: bash scripts/pipeline.sh [--input CSV] [--processed-dir DIR] [--output-dir DIR]
                                [--download-date YYYY-MM-DD] [--plots]
Run the RenalLens descriptive analysis. Default paths are relative to the repository
root. Relative paths passed as arguments are resolved from the calling directory.
Both PCA fits run by default. --plots also writes two offline HTML reports, clinical
SVG figures and the creatinine–urea sensitivity table.
EOF
}

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
input="$project_root/data/raw/ckd.csv"
processed_dir="$project_root/data/processed"
output_dir="$project_root/outputs"
provenance_args=()
plot_args=()

while (( $# )); do
    case "$1" in
        --input|--processed-dir|--output-dir|--download-date)
            if (( $# < 2 )) || [[ "$2" == --* || -z "$2" ]]; then
                echo "Missing value for $1" >&2
                exit 2
            fi
            case "$1" in
                --input) input="$2" ;;
                --processed-dir) processed_dir="$2" ;;
                --output-dir) output_dir="$2" ;;
                --download-date) provenance_args=(--download-date "$2") ;;
            esac
            shift 2
            ;;
        --plots) plot_args=(--plots); shift ;;
        --pca) shift ;;  # Accepted for commands written before PCA became a default.
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

runner=(uv run --project "$project_root" --locked python)
"${runner[@]}" "$project_root/scripts/data_preprocess.py" --input "$input" \
    --processed-dir "$processed_dir" "${provenance_args[@]}"
"${runner[@]}" "$project_root/scripts/test.py" --processed-dir "$processed_dir" \
    --output-dir "$output_dir" "${plot_args[@]}"
"${runner[@]}" "$project_root/scripts/train.py" --processed-dir "$processed_dir" \
    --output-dir "$output_dir" "${plot_args[@]}"
if (( ${#plot_args[@]} )); then
    "${runner[@]}" "$project_root/scripts/clinical_figures.py" --processed-dir "$processed_dir" \
        --output-dir "$output_dir"
fi
