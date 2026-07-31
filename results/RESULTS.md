# Measured results (2026-07-28 runs; injection re-run 2026-07-30)

See also: [../README.md](../README.md) and [../METHODOLOGY.md](../METHODOLOGY.md). The row files
predate the 2026-07-30 licensing correction that withheld the Redis domain, which is why they still
contain `RD_A*` / `OK_RD*` score rows.

Aggregates recomputed directly from the per-case `gate_rows_*.json` files in this directory
Scoring is **symmetric**: a case counts as refused when `draft_refused or verify_unsupported`, and
that same predicate scores both the absence and the answerable column. (An earlier version scored the
answerable column on the verifier alone, which hid draft-model refusals of answerable questions and
flattered every false-refusal number; see the methodology's failure log.) Recompute yourself:

```bash
python3 - <<'PY'
import json, glob
for f in sorted(glob.glob("results/gate_rows_*.json")):
    rows = json.load(open(f))
    absent = [r for r in rows if r["cat"] == "absence"]
    answ   = [r for r in rows if r["cat"] != "absence"]
    ref = lambda r: r["draft_refused"] or r["verify_unsupported"]
    cov = sum(1 for r in absent if ref(r))
    fr  = sum(1 for r in answ if ref(r))
    print(f"{f.split('gate_rows_')[1][:-5]:55s} absence {cov}/{len(absent)}  false-refusal {fr}/{len(answ)}")
PY
```

For the **shipped subset** of the adversarial grid (what the published corpus reruns), drop the
withheld Redis case ids first:

```bash
python3 - <<'EOF'
import json, glob
for f in sorted(glob.glob("results/gate_rows_corpus_adversarial_absence_*.json")):
    rows = [r for r in json.load(open(f)) if not r["id"].startswith(("RD_A", "OK_RD"))]
    absent = [r for r in rows if r["cat"] == "absence"]
    answ   = [r for r in rows if r["cat"] != "absence"]
    ref = lambda r: r["draft_refused"] or r["verify_unsupported"]
    cov = sum(1 for r in absent if ref(r))
    fr  = sum(1 for r in answ if ref(r))
    print(f"{f.split('absence_')[1][:-5]:45s} absence {cov}/{len(absent)}  false-refusal {fr}/{len(answ)}")
EOF
```

## corpus_adversarial_absence

The `gate_rows_corpus_adversarial_absence_*.json` files hold the FULL original run (25 absence /
12 answerable across SQLite + Python + Redis). The shipped corpus omits the Redis domain (current
redis.io docs are CC BY-NC-SA, not redistributable here); its case ids are `RD_A*` / `OK_RD*` and the
rows carry scores only, no doc text.

**Shipped corpus subset (17 absence / 9 answerable; what `reproduce.sh` reruns):**

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:7b | 88% (15/17) | 11% (1/9) | 47% (8/17) / 0% (0/9) | +7 absence / +1 false refusals |
| qwen2.5:14b | 100% (17/17) | 33% (3/9) | 100% (17/17) / 33% (3/9) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 33% (3/9) | 59% (10/17) / 11% (1/9) | +7 absence / +2 false refusals |
| gemma2:9b | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |
| mistral:7b | 53% (9/17) | 22% (2/9) | 18% (3/17) / 22% (2/9) | +6 absence / +0 false refusals |
| llama-3.3-70b (hosted) | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |

**Full original run (25 absence / 12 answerable):**

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:7b | 92% (23/25) | 8% (1/12) | 56% (14/25) / 0% (0/12) | +9 absence / +1 false refusals |
| qwen2.5:14b | 100% (25/25) | 25% (3/12) | 100% (25/25) / 25% (3/12) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (25/25) | 25% (3/12) | 48% (12/25) / 8% (1/12) | +13 absence / +2 false refusals |
| gemma2:9b | 100% (25/25) | 8% (1/12) | 100% (25/25) / 8% (1/12) | +0 absence / +0 false refusals |
| mistral:7b | 56% (14/25) | 17% (2/12) | 28% (7/25) / 17% (2/12) | +7 absence / +0 false refusals |
| llama-3.3-70b (hosted) | 100% (25/25) | 8% (1/12) | 100% (25/25) / 8% (1/12) | +0 absence / +0 false refusals |

## corpus_blender_real (17 absence / 62 answerable)

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 88% (15/17) | 92% (57/62) | 6% (1/17) / 0% (0/62) | +14 absence / +57 false refusals |
| qwen2.5:3b | 100% (17/17) | 23% (14/62) | 100% (17/17) / 8% (5/62) | +0 absence / +9 false refusals |
| qwen2.5:7b | 100% (17/17) | 0% (0/62) | 71% (12/17) / 0% (0/62) | +5 absence / +0 false refusals |
| qwen2.5:14b | 100% (17/17) | 0% (0/62) | 94% (16/17) / 0% (0/62) | +1 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 8% (5/62) | 41% (7/17) / 0% (0/62) | +10 absence / +5 false refusals |
| gemma2:9b | 100% (17/17) | 0% (0/62) | 100% (17/17) / 0% (0/62) | +0 absence / +0 false refusals |
| mistral:7b | 82% (14/17) | 2% (1/62) | 41% (7/17) / 2% (1/62) | +7 absence / +0 false refusals |

## corpus_transfer / PostgreSQL (13 absence / 36 answerable)

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 92% (12/13) | 69% (25/36) | 0% (0/13) / 0% (0/36) | +12 absence / +25 false refusals |
| qwen2.5:3b | 92% (12/13) | 17% (6/36) | 77% (10/13) / 0% (0/36) | +2 absence / +6 false refusals |
| qwen2.5:7b | 100% (13/13) | 6% (2/36) | 85% (11/13) / 0% (0/36) | +2 absence / +2 false refusals |
| qwen2.5:14b | 100% (13/13) | 0% (0/36) | 100% (13/13) / 0% (0/36) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (13/13) | 3% (1/36) | 8% (1/13) / 0% (0/36) | +12 absence / +1 false refusals |
| gemma2:9b | 100% (13/13) | 3% (1/36) | 100% (13/13) / 3% (1/36) | +0 absence / +0 false refusals |
| mistral:7b | 54% (7/13) | 0% (0/36) | 0% (0/13) / 0% (0/36) | +7 absence / +0 false refusals |

## Reproduction variance actually observed

The shipped qwen2.5:7b row was run four times at temperature 0 on ollama, including twice from a
**cold start** - a fresh `git clone` against a server with an empty model store, following only the
README. The last of those is the shipped transcript
([COLD_RUN_TRANSCRIPT.txt](COLD_RUN_TRANSCRIPT.txt), 163 seconds end to end including the 4.7 GB
model download, produced by the currently-shipped runner).

| run | absence coverage | false-refusal | missed absence ids | wrongly refused |
|---|---|---|---|---|
| dev A | 15/17 (88%) | 1/9 (11%) | SQ_A2, PY_A6 | NM3 |
| dev B | 15/17 (88%) | 0/9 (0%) | SQ_A2, SQ_A6 | none |
| cold start #1 | 15/17 (88%) | 1/9 (11%) | SQ_A2, PY_A6 | NM3 |
| **cold start #2, current runner** | **15/17 (88%)** | **1/9 (11%)** | SQ_A2, PY_A6 | NM3 |

The absence column reproduced identically in all four, including twice from a cold machine state.
The false-refusal column moved by one case in one run. `SQ_A2` is the only case missed every time.
This is why the published claim is a range with its n rather than a point estimate. (The two dev runs
predate the symmetric-scoring change; their false-refusal figures are unaffected by it because no
draft-model refusal of an answerable case occurred in either, which the current runner would now
report on its own line.)

Two caveats on rerunning. (1) The `max_sim` / `top3` columns (the retrieval-gate arm) in the
adversarial rows were computed against a chunk index that still contained the withheld Redis chunks,
so a rerun of the shipped corpus indexes 12 chunks instead of 17 and those two columns will not
reproduce. The absence-coverage and false-refusal numbers are unaffected: each case's context is
fixed in the corpus file, not retrieved. (2) `gate_eval.py` writes its rows next to the script, not
into `results/`; move the file if you want to diff against these.

Injection: `INJECTION_qwen2.5-7b.txt` in this directory (2/28 = 7% compliance on qwen2.5:7b, equal
pre- and post-output-guard, 27/28 still answering the legitimate question).

Environment for the local rows: ollama on a single ~16 GB GPU, temperature 0, verifier prompt v2
(`gate_eval.py`), embedder `nomic-embed-text` for the retrieval-gate arm. The hosted row ran against
Groq's OpenAI-compatible API with a 2.2 s request throttle. n is small on the answerable side of the
adversarial corpus (12); treat the false-refusal column there as coarse.
