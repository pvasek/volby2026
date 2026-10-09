#!/usr/bin/env bash
# Re-download official ČSÚ election registries used by extract_candidates.py / cross_reference.py.
set -euo pipefail
cd "$(dirname "$0")/../data/raw/volby_gov"
get() { d=$1; f=$2; sub=$3; mkdir -p "$d"; curl -sS -L --retry 4 -o "$d/$f" "https://volby.gov.cz/opendata/$d/$f"; unzip -o -q "$d/$f" -d "$d/$sub"; }
get kv2026 KV2026reg20261002_csv.zip reg;  get kv2026 KV2026ciselniky20261002_csv.zip cis
get kv2022 KV2022reg20260328_csv.zip reg;  get kv2022 KV2022ciselniky20260328_csv.zip cis
get kv2018 KV2018_reg_20230224_csv.zip reg; get kv2018 KV2018_cisel_20230224_csv.zip cis
get kv2014 KV2014_reg_20230224_csv.zip reg; get kv2014 KV2014_cisel_20230224_csv.zip cis
get kz2016 KZ2016_reg_20230223_csv.zip reg; get kz2016 KZ2016_cisel_20230223_csv.zip cis
get kz2020 KZ2020reg20201004a_csv.zip reg;  get kz2020 KZ2020ciselniky20200918_csv.zip cis
get kz2024 KZ2024reg20240922_csv.zip reg;   get kz2024 KZ2024ciselniky20240922_csv.zip cis
get ps2021 PS2021reg20211111_csv.zip reg;   get ps2021 PS2021ciselniky20211006_csv.zip cis
get ps2025 PS2025reg20251005_csv.zip reg;   get ps2025 PS2025ciselniky20251005_csv.zip cis
