#!/bin/bash
# usage: hlas_ocr_all.sh RAWDIR OCRDIR  -- OCR all voting PDFs, 4 in parallel
RAW="$1"; OCR="$2"; S="$(dirname "$(readlink -f "$0")")"
find "$RAW" -mindepth 2 -maxdepth 2 -iname 'v*sledk*.pdf' -print0 | sort -z | while IFS= read -r -d '' f; do
  sess="$(basename "$(dirname "$f")")"; stem="$(basename "$f" .pdf)"
  printf '%s\0%s\0' "$f" "$OCR/$sess/$stem"
done | xargs -0 -n2 -P4 python3 -I "$S/hlas_ocr.py"
