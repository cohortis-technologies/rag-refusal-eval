# rag-refusal-eval

A reproducible harness for measuring whether a retrieval-augmented (RAG) system **refuses when the
answer is not in the retrieved material**, reported honestly in both directions:

- **absence coverage**: of genuinely-unanswerable questions, the fraction refused (higher is better);
- **false-refusal**: of answerable questions, the fraction wrongly refused (lower is better).

Every number here carries its n, and no absence number appears without its false-refusal pair,
because either number alone is trivially gameable: a system that refuses everything scores 100%
absence coverage, and a system that answers everything scores 0% false-refusal. Both show up below,
in real models.

## The numbers

Mechanism under test: two-pass verification. A model drafts an answer from the retrieved context;
a second cheap call judges one thing (does the material actually contain the answer?); UNSUPPORTED
becomes a deterministic refusal. Model-based, so there is no retrieval-similarity threshold to tune,
and (measured, section c of [METHODOLOGY.md](METHODOLOGY.md)) thresholds do not transfer between
corpora anyway.

**Scoring is symmetric**: a case counts as refused whenever the system declines, whether the draft
model refused or the verifier overrode it, and the same rule scores both columns. This matters -
an earlier version of this harness scored coverage on either layer but false-refusal on the verifier
alone, which flattered the system in both directions at once. See the failure log.

**The baseline column is the one to read first.** It is what the model does with the mechanism turned
off, in *both* directions. Where it already equals the coverage column, the verification pass
contributed nothing on that corpus and the number is a property of the model, not of this repo's
mechanism. Where the verifier does add absence coverage, look at what it added to the false-refusal
column in the same row: on qwen2.5:0.5b/Blender it buys +14 absence cases and costs +57 false
refusals, which is the whole argument for never reading one column alone.

**Adversarial absence corpus as shipped** (17 genuinely-silent cases across SQLite / Python docs,
9 answerable controls; every absence case annotated with *why* the material is silent):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:7b | 88% (15/17) | 11% (1/9) | 47% (8/17) / 0% (0/9) | +7 absence / +1 false refusals |
| qwen2.5:14b | 100% (17/17) | 33% (3/9) | 100% (17/17) / 33% (3/9) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 33% (3/9) | 59% (10/17) / 11% (1/9) | +7 absence / +2 false refusals |
| gemma2:9b | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |
| mistral:7b | 53% (9/17) | 22% (2/9) | 18% (3/17) / 22% (2/9) | +6 absence / +0 false refusals |
| llama-3.3-70b (hosted) | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |

**Standard documentation Q&A**, Blender Manual (17 absence / 62 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 88% (15/17) | 92% (57/62) | 6% (1/17) / 0% (0/62) | +14 absence / +57 false refusals |
| qwen2.5:3b | 100% (17/17) | 23% (14/62) | 100% (17/17) / 8% (5/62) | +0 absence / +9 false refusals |
| qwen2.5:7b | 100% (17/17) | 0% (0/62) | 71% (12/17) / 0% (0/62) | +5 absence / +0 false refusals |
| qwen2.5:14b | 100% (17/17) | 0% (0/62) | 94% (16/17) / 0% (0/62) | +1 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 8% (5/62) | 41% (7/17) / 0% (0/62) | +10 absence / +5 false refusals |
| gemma2:9b | 100% (17/17) | 0% (0/62) | 100% (17/17) / 0% (0/62) | +0 absence / +0 false refusals |
| mistral:7b | 82% (14/17) | 2% (1/62) | 41% (7/17) / 2% (1/62) | +7 absence / +0 false refusals |

and PostgreSQL docs (13 absence / 36 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 92% (12/13) | 69% (25/36) | 0% (0/13) / 0% (0/36) | +12 absence / +25 false refusals |
| qwen2.5:3b | 92% (12/13) | 17% (6/36) | 77% (10/13) / 0% (0/36) | +2 absence / +6 false refusals |
| qwen2.5:7b | 100% (13/13) | 6% (2/36) | 85% (11/13) / 0% (0/36) | +2 absence / +2 false refusals |
| qwen2.5:14b | 100% (13/13) | 0% (0/36) | 100% (13/13) / 0% (0/36) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (13/13) | 3% (1/36) | 8% (1/13) / 0% (0/36) | +12 absence / +1 false refusals |
| gemma2:9b | 100% (13/13) | 3% (1/36) | 100% (13/13) / 3% (1/36) | +0 absence / +0 false refusals |
| mistral:7b | 54% (7/13) | 0% (0/36) | 0% (0/13) / 0% (0/36) | +7 absence / +0 false refusals |

The original private run of the adversarial corpus had a third domain (Redis, 8 more absence cases;
qwen2.5:7b 92% / 8% at n=25/12). It is withheld because current redis.io documentation is
CC BY-NC-SA (NonCommercial), which we cannot honestly redistribute; the withheld cases' score rows
(no text) are in `results/` and both grids are in [results/RESULTS.md](results/RESULTS.md). The
licensing catch is itself part of the story: verify the license page, not the assumption.

### What the data actually supports

1. **The mechanism earns its keep on small models and does nothing on capable ones.** On the
   adversarial corpus it takes qwen2.5:7b from 47% to 88% absence coverage and llama3.1:8b from 59%
   to 100%, but adds exactly zero for qwen2.5:14b, gemma2:9b and the hosted 70b, which already
   refuse every absence case unaided. On PostgreSQL it takes llama3.1:8b from 8% to 100%. If you can
   afford a large model, the interesting question is not this mechanism; if you are running a 7B
   locally, it roughly doubles absence coverage.
2. **Easy corpora compress differences; they do not erase them.** On the standard corpora every
   model at 3B and above *except* mistral:7b reaches 92-100% absence coverage (mistral is the
   exception at 82% on Blender and 54% on PostgreSQL), and the rest separate mainly on false-refusal
   (0% to 23%). The adversarial corpus separates the absence column too, but modestly for capable
   models: it moves qwen2.5:7b down by two cases out of 17 and leaves 14b, gemma2 and the 70b at
   100%. State this as "an easy corpus barely separates capable models on the absence axis", not as
   a large hidden effect.
3. **Family beats size, and the failure is not one-directional.** mistral:7b and qwen2.5:7b are the
   same size; mistral gets 53% absence coverage against 88%. Under symmetric scoring mistral is also
   *not* the permissive model an earlier version of this README described - it wrongly refuses 22%
   (2/9) of answerable questions while still missing 47% of the unanswerable ones. It is worse in
   both directions, not trading one for the other. Note also that mistral's weakness was already
   visible on the easy PostgreSQL corpus (54%), so the hard corpus confirmed it rather than
   revealing it.

Caveats: n on the shipped hard set is small (17 absence, 9 answerable), so one case is 5.9% of the
absence column and 11.1% of the false-refusal column; every number is model- and corpus-specific;
re-run on any change. Full tables, limits, and the failure log: [METHODOLOGY.md](METHODOLOGY.md).

## Seven ways this measurement was wrong (some found by outside review)

The most useful part of this project is the sequence of ways the measurement was wrong before it was
right. Two of the entries below were found by an adversarial reviewer reading the code, not by us -
which is the honest version of the story and the reason the list is worth reading. Each is written up
in [METHODOLOGY.md](METHODOLOGY.md#2-the-failures-in-the-order-they-happened):

- The **hand-authored corpus ran easy**: 95% (21/22) on self-written docs against 86% (n=79) on real
  documentation, on the same keyword scorer. A corpus you author to test your system is an upper
  bound on your system.
- The **injection defence scored a false 0%**: the Python eval's `\s` neutralised a Unicode-space
  payload the production matcher would have missed. The honest number is 7% (2/28 on qwen2.5:7b,
  re-run 2026-07-30, artifact in [results/INJECTION_qwen2.5-7b.txt](results/INJECTION_qwen2.5-7b.txt);
  the runner now reports compliance both pre- and post-output-guard so the guard cannot hide a leak,
  and one canary that could never fire was repointed at a string the system prompt actually
  contains). If your eval and your production code normalise text differently, your eval is
  measuring the eval.
- The **retrieval-confidence threshold did not transfer**: a 0.60 cosine cutoff gave 35% absence
  coverage (6/17) on one corpus and 69% (9/13) on another, both at 0% false-refusal (0/62, 0/36) -
  cheap and ineffective. It only became effective by becoming expensive. That is why the shipped
  mechanism has no threshold.
- The **truncation guard was correct and useless**: it never damaged a grounded answer in the internal run that measured it (0 false positives in 17 grounded answers; that run predates this repo and its rows are not shipped), and its real coverage is near zero because the failure it targets usually appears as a paraphrased refusal it cannot match.
- The **scoring rule was asymmetric in the system's favour**: absence coverage counted a refusal from
  either layer, but false-refusal counted only the verifier's. Draft-model refusals of answerable
  questions were therefore invisible. Under the corrected symmetric rule mistral:7b's "0%
  false-refusal" becomes 22% and two other models move from 22% to 33%. Every number in this repo is
  now scored with one rule applied to both columns.
- The **mechanism's own baseline was never published**, so "100% absence coverage" read as a result of
  the verification pass when for three of six models the base model scored 100% unaided. Every table
  now carries the no-mechanism baseline next to the coverage number.
- The **mislabeled absence cases produced a false 50%**: 4 of 8 "absence" cases were actually
  answerable ("what is the SQLite equivalent of SHOW DATABASES?" against material that contains
  `.databases` is answerable). Reading the individual missed cases, not the aggregate, caught it.
  The discipline that came out of it: **if the material says "there is no X, use Y", the question is
  answerable, not absent.** Every absence case in the adversarial corpus now carries a `why` field
  justifying genuine silence. **Scope caveat**: that audit covers the adversarial corpus only. The 30
  absence labels in the two standard corpora predate the discipline and have not been re-audited case
  by case; treat those numbers as resting on unaudited labels.

## What is in the repo

| file | what |
|---|---|
| `gate_eval.py` | the main runner: retrieval-gate threshold sweep + two-pass verification, both directions, per-case JSON rows |
| `run_eval.py` | the grounded-generation eval (deterministic scoring, refusal detection, injection neutralisation, ollama + OpenAI-compatible callers) |
| `run_retrieval_eval.py` | recall@k for embedding models (retrieval scored separately from generation) |
| `injection_eval.py` | 28-attack prompt-injection set for the RAG answer path |
| `demo_grounding_verify.py` | the whole two-pass idea in ~50 standalone lines |
| `corpus_blender_real.py` | standard corpus 1: Blender Manual excerpts (CC-BY-SA 4.0) + cases |
| `corpus_transfer.py` | standard corpus 2: PostgreSQL docs excerpts + cases (the transfer test) |
| `corpus_adversarial_absence.py` | the hard corpus: 17 genuinely-silent cases with per-case rationale, 2 domains |
| `sweep.sh` | pull-and-run a model list over a corpus list |
| `results/` | per-case JSON rows for every (model, corpus) cell above + `RESULTS.md` + the injection run |

The published rows carry per-case *scores*, not model outputs (id, category, top-1/top-3 similarity,
whether the draft refused, whether the verifier said UNSUPPORTED). That is enough to recompute every
aggregate here and to see exactly which case ids moved, but not to re-read the answers themselves;
regenerate those locally with `gate_eval.py`, which prints them. One caveat on the shipped rows'
`draft_ok` column: it comes from a keyword scorer that marks some *correct* refusals as not-ok when
the refusal echoes a keyword from the question (9 such cases for qwen2.5:7b), so treat `draft_ok` as
a coarse signal only. It is not used in any absence-coverage or false-refusal number on this page.

## Reproduce it

Requirements: Python 3 (stdlib only, no venv or pip needed), plus `bash`, `curl` and the `ollama`
CLI for `reproduce.sh`; a running [ollama](https://ollama.com). Defaults assume
`http://localhost:11434`; for anything else set `OLLAMA_URL` (and `OLLAMA_HOST` so the `ollama` CLI
pulls to the same server). The embedding endpoint is derived from `OLLAMA_URL`, so one variable is
enough; `OLLAMA_EMBED_URL` overrides it separately if your embedder lives elsewhere.

Cold-start cost: pulling `qwen2.5:7b` (4.7 GB) and `nomic-embed-text` (274 MB) dominates. A measured
cold run on a consumer GPU took **163 seconds end to end**, model download included; the full
transcript, produced by the currently-shipped runner, is
[results/COLD_RUN_TRANSCRIPT.txt](results/COLD_RUN_TRANSCRIPT.txt).

```bash
./reproduce.sh                 # pulls qwen2.5:7b + nomic-embed-text, runs the adversarial corpus
```

or by hand, any model, any corpus:

```bash
ollama pull qwen2.5:7b && ollama pull nomic-embed-text
python3 gate_eval.py corpus_adversarial_absence qwen2.5:7b     # writes rows next to the script
MODELS="qwen2.5:7b mistral:7b" CORPORA="corpus_adversarial_absence" ./sweep.sh   # the full grid
```

Hosted comparison (any OpenAI-compatible endpoint):

```bash
GROQ_API_KEY=... python3 gate_eval.py corpus_adversarial_absence groq:llama-3.3-70b-versatile
```

Note: the drafting system prompt names the assistant persona of the production system this was
extracted from ("You are Cohortis, a calm and rigorous study companion..."). It is kept verbatim
because it is the exact prompt the published numbers were measured with; the refusal-detection and
injection-leak checks key on it.

## Prior art (read this first; none of this is new)

This is an independent, stdlib-only reimplementation of standard groundedness and abstention
measurement, applied to a hand-built adversarial absence corpus, with a fully local reproduction path
and a documented log of the ways the measurement was wrong first. It is **not** a replication in the
strict sense: it does not reproduce any specific published number, and it should not be read as
claiming to. It claims no novelty. The relevant prior art:

- **Unanswerable-question detection**: SQuAD 2.0 (Rajpurkar et al., 2018) started it.
- **Sufficient context and retrieval gating**: "Sufficient Context" (Joren et al., ICLR 2025) asks
  the same question this harness measures - does the retrieved context actually contain enough to
  answer - and CRAG (Yan et al., 2024) is the retrieval-confidence-gating family whose threshold
  approach we independently found does not transfer between corpora.
- **Abstention benchmarks**: AbstentionBench (Kirichenko et al., 2025, 20 datasets); RefusalBench
  (Muhamed et al., 2025), which uses a generator-verifier pipeline to *construct* selective-refusal
  test cases for grounded models (construction-time QA, distinct from the runtime draft-then-verify
  mechanism measured here); GaRAGe (Sorodoc et al., 2025), which reports true/false-positive
  deflection (refusal) rates for grounded RAG; the RagRefuse benchmark (Maskey et al., 2025,
  "Steering Over-refusals Towards Safety in RAG", safety-side over-refusal); and the TACL survey
  "Know Your Limits: A Survey of Abstention in Large Language Models" (Wen et al., 2025).
- **Production tooling**: Ragas (noise sensitivity), TruLens (RAG triad), Vectara HHEM,
  Patronus Lynx - groundedness/faithfulness measurement is standard in funded tools.
- **Closest single artifact**: Goutam Adwant, "Local RAG Refusal Calibration Benchmark and Results",
  IEEE DataPort, DOI [10.21227/m670-k992](https://doi.org/10.21227/m670-k992), created June 2026.
  The dataset page describes itself as the reproducibility artifact for a manuscript titled *"When
  Good Retrieval Is Not Enough: Prompt Design Outperforms Retrieval-Score Gating in Local RAG
  Refusal"*, covering SQuAD v2, HotpotQA and a bounded Natural Questions stress test on a local
  Ollama server, reporting coverage, unsupported-answer risk, utility and latency. **That title
  states, in different words, the same negative result this repo reports in section 2c** (a
  retrieval-score threshold underperforms and does not transfer; prompt/verification-level handling
  is what works). We reached it independently on different corpora, and we found the artifact only
  after the fact - it is prior art for that finding, and it is cited here as such. Honest status
  note: the artifact is self-submitted and its associated manuscript could not be found published
  anywhere (no Crossref record, no preprint) as of 2026-07-30, so treat "IEEE Access manuscript" as
  the author's own description rather than a verified publication. The archive itself is
  login-gated, so we could not check whether it measures a false-refusal counterpart.

What this repo offers over reading those: a small, fully-inspectable, stdlib-only harness you can run
on your own corpus this afternoon; an adversarial absence corpus with a per-case rationale for why
the material is silent; both-directions reporting **printed by the harness by default, in both the
mechanism and baseline rows**, so dropping a column is a deliberate act rather than an oversight (the discipline is not ours - GaRAGe reports
true/false-positive deflection rates, and risk-coverage curves are standard in selective prediction);
a published no-mechanism baseline so the mechanism's marginal value is visible; and a written record
of the ways the measurement went wrong first.

## Licensing

- **Harness code** - `gate_eval.py`, `run_eval.py`, `run_retrieval_eval.py`, `injection_eval.py`,
  `demo_grounding_verify.py`, `reproduce.sh`, `sweep.sh`: Apache-2.0 (see [LICENSE](LICENSE)).
  The three `corpus_*.py` files are **not** Apache-2.0; each carries its own SPDX identifier
  matching the documentation it excerpts.
- **Corpus files**: each carries the license of the documentation it excerpts; see
  [CORPUS_LICENSES.md](CORPUS_LICENSES.md). In particular `corpus_blender_real.py` (Blender Manual)
  is a CC-BY-SA 4.0 derivative and remains under CC-BY-SA 4.0; the Redis domain was withheld
  entirely (CC BY-NC-SA, not redistributable here).

## Provenance

Extracted from the eval suite of [Cohortis](https://cohortis.io), a Discord-native tutor designed to
answer students only from uploaded course material and to refuse otherwise. The production system
runs the same two-pass verifier this harness measures, which is why the numbers above are the
honest bound on that design rather than a claim that it always succeeds: on the adversarial corpus
it still answered 2 of 17 genuinely-unanswerable questions.
