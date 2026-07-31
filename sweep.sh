#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Model sweep for the grounding gate: absence coverage AND false-refusal (both directions) per model,
# over the real-doc corpora, plus the retrieval-confidence-gate threshold sweep. Pulls each model, runs
# gate_eval.py per (model, corpus), appends to a timestamped SWEEP file. A failed pull skips that
# model instead of aborting the sweep. Override MODELS / CORPORA / OLLAMA_URL / OLLAMA_EMBED_URL via env.
set -uo pipefail
cd "$(dirname "$0")"
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/api/chat}"
export OLLAMA_EMBED_URL="${OLLAMA_EMBED_URL:-http://localhost:11434/api/embed}"
OUT="SWEEP_$(date -u +%Y%m%dT%H%M%SZ).txt"
MODELS="${MODELS:-qwen2.5:0.5b qwen2.5:3b qwen2.5:7b qwen2.5:14b}"
CORPORA="${CORPORA:-corpus_blender_real corpus_transfer}"

echo "# grounding model sweep  models=[$MODELS]  corpora=[$CORPORA]  $(date -u +%FT%TZ)" | tee "$OUT"
echo "## embedder (retrieval-gate arm)" | tee -a "$OUT"
ollama pull nomic-embed-text >>"$OUT" 2>&1 || echo "WARN: nomic-embed-text pull failed (gate arm will error)" | tee -a "$OUT"

for m in $MODELS; do
  echo "" | tee -a "$OUT"; echo "## pull $m" | tee -a "$OUT"
  if ! ollama pull "$m" >>"$OUT" 2>&1; then
    echo "SKIP $m (pull failed)" | tee -a "$OUT"; continue
  fi
  for c in $CORPORA; do
    echo "" | tee -a "$OUT"; echo "### gate_eval  model=$m  corpus=$c" | tee -a "$OUT"
    python3 gate_eval.py "$c" "$m" >>"$OUT" 2>&1 || echo "FAIL gate_eval $m $c" | tee -a "$OUT"
  done
done
echo "" | tee -a "$OUT"; echo "# sweep complete -> $OUT" | tee -a "$OUT"
