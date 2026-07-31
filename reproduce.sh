#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# One-command reproduction of the headline adversarial-corpus row (qwen2.5:7b).
# Requirements: python3 (stdlib only) and a running ollama (https://ollama.com).
# Takes a few minutes on a GPU; longer on CPU. Prints both directions (absence coverage AND
# false-refusal) and writes per-case rows to gate_rows_corpus_adversarial_absence_qwen2.5-7b.json.
set -euo pipefail
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v ollama  >/dev/null || { echo "ollama is required (https://ollama.com)"; exit 1; }
OLLAMA_API="${OLLAMA_URL:-http://localhost:11434/api/chat}"
BASE="${OLLAMA_API%/api/*}"
curl -sf --max-time 5 "$BASE/api/version" >/dev/null || {
  echo "ollama server is not responding at $BASE (start it with: ollama serve)"; exit 1; }

echo "==> pulling models (qwen2.5:7b draft/verify, nomic-embed-text for the retrieval-gate arm)"
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

echo "==> running the adversarial absence corpus (17 silent / 9 answerable)"
python3 gate_eval.py corpus_adversarial_absence qwen2.5:7b

echo ""
echo "Compare against results/RESULTS.md (expected: ~88% absence coverage, ~11% false-refusal;"
echo "exact counts can flip by one case run-to-run at temperature 0 across ollama versions)."
