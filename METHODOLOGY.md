# Measuring grounding: a method, and what it taught us

Written for someone who wants to measure whether their own retrieval-augmented system answers only
from the retrieved material and refuses when it can't. Not marketing. The harness is this repo
(stdlib Python, hits an ollama or OpenAI-compatible HTTP endpoint); the numbers are from running it. **Every number carries its n, and no number appears without
its false-refusal pair.** The failures section is the most valuable part; most write-ups omit theirs, and
one of ours is a mistake the method caught in its own author.

## 0. Prior art, before anything else

None of the ideas here are new, and this document is sometimes read on its own, so the pointer goes
first rather than in a companion file. Unanswerable-question detection begins with SQuAD 2.0
(Rajpurkar et al., 2018). Abstention is an established subfield: AbstentionBench (Kirichenko et al.,
2025), RefusalBench (Muhamed et al., 2025), GaRAGe (Sorodoc et al., 2025, which reports
true/false-positive deflection rates), and the TACL survey "Know Your Limits: A Survey of Abstention
in Large Language Models" (Wen et al., 2025). Draft-then-verify is likewise standard: Self-RAG's
critique tokens (Asai et al., ICLR 2024), Chain-of-Verification (arXiv:2309.11495), and MiniCheck (EMNLP 2024) are the same shape as the
mechanism measured here; "Sufficient Context" (Joren et al., ICLR 2025) is the closest published
treatment of the exact question this harness asks - whether the retrieved context contains enough to
answer at all - and CRAG (Yan et al., 2024) is the retrieval-confidence-gating family whose threshold
approach section 2c reports failing to transfer, and groundedness scoring ships in
Ragas, TruLens, Vectara HHEM and Patronus Lynx. Trading coverage against error is selective
prediction, which long predates LLMs. The closest single artifact is Adwant's local-Ollama refusal
calibration benchmark (IEEE DataPort, DOI 10.21227/m670-k992), whose stated thesis matches the
negative result in section 2c below. Full citations and honest status notes: the repo README.

What follows is a practitioner's measurement record, not a contribution to that literature.

## 1. The problem

Two failure modes matter and neither is caught by "does the answer look right":

- **Unreliable refusal.** When the answer is genuinely not in the retrieved material, a model often
 answers anyway from its training priors. The stronger the prior, the more confident and wrong the
 fabrication. "Refuses when it doesn't know" is a property you must measure, not assume.
- **Silent blend-and-contradict.** A model can give a correct grounded answer and then append ungrounded
 "however, generally..." content that reads as part of the same answer. The reader cannot tell which
 sentence came from their material and which came from training. It is invisible at the surface; you
 only see it by scoring against the source.

Both are about the *absence* case (the material does not contain the answer). That is where users get
hurt, and it is the category every easy eval under-weights.

## 2. The failures, in the order they happened

These are the most useful part. Each one is a way the measurement lied until it was fixed.

**a. The hand-authored corpus ran easy.** The first corpus was three documents we wrote, with questions
we wrote. It scored 21/22 (95%) on `run_eval.py`'s exact-match-plus-refusal scorer (the corpus still
ships in `run_eval.py`; reproduce with `python3 run_eval.py qwen2.5:7b`). The same scorer on real
documentation (Blender Manual, n=79) gave 86% in that run; recomputing the closest equivalent from
the shipped Blender rows today gives 85% (67/79), a case apart. No artifact of the original 22-case
run was kept, which is itself a small instance of the same lesson - keep the transcript. Both figures come from that keyword scorer, which is
coarser than the both-directions numbers in section 4 and which marks some correct refusals as
failures - treat the 9-point gap as directional evidence that self-authored corpora run easy, not as
a precise measurement. A corpus you author to test your system is an upper bound on your system. Use
real, licensed documentation; treat any self-authored number as optimistic.

**b. The injection defence scored a false 0%.** An early one-layer pass reported 0% jailbreak compliance
(perfect). Adversarial review showed it was measured dishonestly: a payload spaced with non-breaking /
Unicode spaces bypassed the production Java `\s` (ASCII whitespace) matcher while the Python eval's `\s`
neutralised it, so the eval scored "neutralised" a payload production would not have caught. The same
pass was also over-broad, corrupting legitimate material ("act as a catalyst"). The honest number after
fixing both (NFKC normalisation to close the bypass, tightened patterns, an output-side leak guard) is
**7% compliance (2/28) on qwen2.5:7b**, not 0% (re-run 2026-07-30; artifact in `results/`). Two
further eval defects surfaced in an adversarial review and were fixed before that re-run: one attack
scored compliance on a canary string the system prompt does not contain, so it could never fire; and
the runner scored the answer *after* the output-side leak guard had already scrubbed it, so a
successful prompt leak could be cleaned before scoring. The runner now reports compliance both
pre-guard and post-guard. They agree at 2/28 here, which is the evidence that the guard is not
hiding a leak rather than an assumption that it isn't. Lesson: if your eval and your production code normalise text
differently, your eval is measuring the eval.

**c. The retrieval-confidence threshold did not transfer between corpora.** A tempting cheap mechanism:
embed the question, take the top-1 cosine similarity against the chunk index, refuse below a threshold,
never call the model. It failed on the evidence: the absent and answerable similarity distributions
*overlap* on both corpora, and the threshold that looked decent on one did not transfer to the other (a
0.60 cutoff gave ~35% absence coverage on one corpus, ~69% on another, both at 0% false-refusal;
the cheapest cutoff reaching 100% coverage on the 0.05 grid cost 29% false-refusal on Blender
(18/62) and 8% on PostgreSQL (3/36)).
Quoting the rejected mechanism at its worst threshold without its false-refusal pair would be the
same sin this document is about, so: at 0.60 the gate was cheap and ineffective, and it only became
effective by becoming expensive. A constant cutoff cannot reach
high absence coverage without heavy false-refusal. This is why the shipped mechanism is model-based (no
threshold).

**d. The truncation guard was nearly inert.** A guard truncates content a model appends *after* the exact
mandated refusal sentence. False-positive rate on grounded answers: 0/17 (it never damaged a real
answer). But its real coverage is near zero, because the failure it targets mostly appears as a
*paraphrased* refusal the exact-string guard doesn't match. A correct, harmless, almost useless guard.
Keep it as a cheap backstop; do not count it as the absence fix.

**e. The mislabeled absence cases produced a false 50% (the method catching its own author).** Building a
harder absence corpus, the first run of a 70B model scored 50% absence coverage and looked alarming.
Reading the *individual missed cases* instead of accepting the number showed the corpus was wrong, not
the model: 4 of 8 "absence" cases were actually **answerable**. A question like "what is the SQLite
equivalent of `SHOW DATABASES`?" against material that contains `.databases` is not absent - the grounded
answer is "use `.databases`," and the model giving it was scored as a failed refusal. The discipline that
fixes this: **a case is genuine absence only if the material is truly silent; if the material says "there
is no X, use Y," the question is answerable.** After reclassifying the four, the corpus was rebuilt to 25
genuinely-silent cases across three domains, each annotated with *why* the material is silent (the
published version ships two of the three domains; the third was withheld for licensing, itself a
second instance of verify-the-licence-page). The
mechanism that caught it was reading the failures, plus the both-directions rule (the "false 50%" was
paired with a false-refusal number that didn't fit). This is the single most important habit in the whole
method: **read the missed cases; do not accept the aggregate.**

**f. The scoring rule was asymmetric in the system's favour.** Absence coverage counted a refusal
from either layer (the draft model refusing, or the verifier overriding), but false-refusal counted
only the verifier's. A draft model that refused an answerable question was therefore scored as
neither a coverage success nor a false refusal - it simply vanished. This flattered the system in
both columns at once, in a harness whose stated purpose is to stop exactly that. Under the corrected
symmetric rule (a refusal is a refusal, same rule both columns) mistral:7b's headline "0%
false-refusal" becomes **22% (2/9)**, and qwen2.5:14b and llama3.1:8b move from 22% to **33% (3/9)**
on the shipped adversarial corpus. The qwen2.5:7b headline numbers did not move. Lesson: write the
scoring rule as one predicate and apply it to both columns; if the two columns need different
predicates, that asymmetry is a finding, not an implementation detail.

**g. The mechanism's own baseline was missing from every published table.** The runner computed
"model-only absence refusals (no mechanism)" and printed it to the terminal, and no document
published it. With it published, three of the six models in the headline table (qwen2.5:14b,
gemma2:9b, hosted llama-3.3-70b) turn out to reach 100% absence coverage **unaided** - the
verification pass contributes exactly nothing for them on this corpus. It contributes +7 absence cases for
qwen2.5:7b on the adversarial corpus, and +12 for llama3.1:8b on PostgreSQL. Publishing a mechanism's result without its
no-mechanism baseline is not a measurement, it is an advertisement. This one was caught by an
adversarial reviewer reading the runner's source, not by us.

## 3. What worked

- **Two-pass verification.** Draft the answer with the model, given the retrieved context. Then a cheap
 second call judges one thing: does the material actually contain the answer to this question? A
 one-word SUPPORTED / UNSUPPORTED verdict; UNSUPPORTED becomes a deterministic refusal. It is
 model-based, so there is no numeric threshold to tune or transfer (unlike failure c). Fail *open* on an
 off-format verdict (only a leading "unsupported" token refuses), so a verbose judge doesn't silently
 refuse everything.
- **Both-directions reporting, always.** Report absence coverage (of unanswerable questions, the fraction
 refused) AND false-refusal (of answerable questions, the fraction wrongly refused) together, every
 time, with n. Reporting only one direction is how a model that refuses everything scores "100%
 grounded." This rule caught failure (e) and exposed the model floor below.
- **Real, licensed corpora.** Blender Manual (CC-BY-SA 4.0), PostgreSQL docs (PostgreSQL License),
 and for the hard set SQLite (public domain) and Python (PSF). Correction 2026-07-30: the Redis
 domain was built believing redis.io docs were CC-BY-SA; they are CC BY-NC-SA 4.0 (NonCommercial),
 so the Redis cases are internal-only and withheld from the public corpus. Keep the licence
 discipline; verify the licence page, not the assumption.
- **Adversarial absence cases.** Three shapes, the ones where users get hurt: adjacent-but-different (the
 material covers a neighbour of the asked feature), wrong-prior (a phrasing that triggers a confident
 training-prior answer), and partial (the material covers half; the honest answer refuses the other
 half). These are what separate models that easy corpora rate identically (section 5).

## 4. The numbers (each with n; each with its false-refusal pair; each with its baseline)

The mechanism is the two-pass verifier. "Absence coverage" = of genuinely-unanswerable questions, the
fraction refused. "False-refusal" = of answerable questions, the fraction wrongly refused. **Both
columns use one rule**: the system refused, whichever layer did it.

The **baseline** column is what the draft model does with the verification pass turned off, in both
directions, and "verifier adds" is the difference in both directions. Read those before the first two
columns: where the baseline already equals the coverage, the mechanism did nothing on that corpus,
and where the verifier adds absence coverage it usually adds false refusals too. That trade is the
whole point of reporting the pair.

**Standard corpora, Blender Manual** (17 absence / 62 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 88% (15/17) | 92% (57/62) | 6% (1/17) / 0% (0/62) | +14 absence / +57 false refusals |
| qwen2.5:3b | 100% (17/17) | 23% (14/62) | 100% (17/17) / 8% (5/62) | +0 absence / +9 false refusals |
| qwen2.5:7b | 100% (17/17) | 0% (0/62) | 71% (12/17) / 0% (0/62) | +5 absence / +0 false refusals |
| qwen2.5:14b | 100% (17/17) | 0% (0/62) | 94% (16/17) / 0% (0/62) | +1 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 8% (5/62) | 41% (7/17) / 0% (0/62) | +10 absence / +5 false refusals |
| gemma2:9b | 100% (17/17) | 0% (0/62) | 100% (17/17) / 0% (0/62) | +0 absence / +0 false refusals |
| mistral:7b | 82% (14/17) | 2% (1/62) | 41% (7/17) / 2% (1/62) | +7 absence / +0 false refusals |

**Standard corpora, PostgreSQL docs** (13 absence / 36 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:0.5b | 92% (12/13) | 69% (25/36) | 0% (0/13) / 0% (0/36) | +12 absence / +25 false refusals |
| qwen2.5:3b | 92% (12/13) | 17% (6/36) | 77% (10/13) / 0% (0/36) | +2 absence / +6 false refusals |
| qwen2.5:7b | 100% (13/13) | 6% (2/36) | 85% (11/13) / 0% (0/36) | +2 absence / +2 false refusals |
| qwen2.5:14b | 100% (13/13) | 0% (0/36) | 100% (13/13) / 0% (0/36) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (13/13) | 3% (1/36) | 8% (1/13) / 0% (0/36) | +12 absence / +1 false refusals |
| gemma2:9b | 100% (13/13) | 3% (1/36) | 100% (13/13) / 3% (1/36) | +0 absence / +0 false refusals |
| mistral:7b | 54% (7/13) | 0% (0/36) | 0% (0/13) / 0% (0/36) | +7 absence / +0 false refusals |

**Hard corpus as shipped** (adversarial absence, SQLite + Python, 17 absence / 9 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:7b | 88% (15/17) | 11% (1/9) | 47% (8/17) / 0% (0/9) | +7 absence / +1 false refusals |
| qwen2.5:14b | 100% (17/17) | 33% (3/9) | 100% (17/17) / 33% (3/9) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (17/17) | 33% (3/9) | 59% (10/17) / 11% (1/9) | +7 absence / +2 false refusals |
| gemma2:9b | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |
| mistral:7b | 53% (9/17) | 22% (2/9) | 18% (3/17) / 22% (2/9) | +6 absence / +0 false refusals |
| llama-3.3-70b (hosted) | 100% (17/17) | 11% (1/9) | 100% (17/17) / 11% (1/9) | +0 absence / +0 false refusals |

**Hard corpus, full private run** (adds the withheld Redis domain, 25 absence / 12 answerable):

| model | absence coverage | false-refusal | baseline (absence / FR) | verifier adds |
|---|---|---|---|---|
| qwen2.5:7b | 92% (23/25) | 8% (1/12) | 56% (14/25) / 0% (0/12) | +9 absence / +1 false refusals |
| qwen2.5:14b | 100% (25/25) | 25% (3/12) | 100% (25/25) / 25% (3/12) | +0 absence / +0 false refusals |
| llama3.1:8b | 100% (25/25) | 25% (3/12) | 48% (12/25) / 8% (1/12) | +13 absence / +2 false refusals |
| gemma2:9b | 100% (25/25) | 8% (1/12) | 100% (25/25) / 8% (1/12) | +0 absence / +0 false refusals |
| mistral:7b | 56% (14/25) | 17% (2/12) | 28% (7/25) / 17% (2/12) | +7 absence / +0 false refusals |
| llama-3.3-70b (hosted) | 100% (25/25) | 8% (1/12) | 100% (25/25) / 8% (1/12) | +0 absence / +0 false refusals |

Caveats: n is small on both hard grids. On the shipped 17/9 subset one case is 5.9% of the absence
column and 11.1% of the false-refusal column; on the full 25/12 run, 4.0% and 8.3%. The answerable
set is the smaller one, so the false-refusal column is the noisier of the two. All numbers are
model-specific and corpus-specific; re-run on any change.

## 5. The general result: easy evals cannot separate capable models, and family beats size

On the easy corpora, qwen2.5:7b, 14b, llama3.1:8b, and gemma2:9b all score **100% absence coverage**.
They are not indistinguishable, though: they separate on the other axis, with pooled false-refusal
running 0% to 6% across them (llama3.1:8b is the outlier at 5/62 on Blender). The absence column is
what the easy corpora cannot separate. On the hard corpus they separate, but state the effect honestly: **one** of those
four moves (7b to 92% on the full run, 88% on the shipped subset), by two cases, while 14b /
llama3.1:8b / gemma2:9b / the hosted 70b stay at 100%. So the defensible claim is the weaker one: an
easy corpus cannot distinguish capable models at all, and a hard one begins to, at a magnitude this
n can only bound loosely. Do not sell it as a large effect.

And the differences are **not mainly about size**. `mistral:7b` and `qwen2.5:7b` are the same size;
mistral gets 56% hard-absence and qwen 92%. `llama3.1:8b` and `gemma2:9b` reach 100% at 8-9B. Family and
training matter at least as much as parameter count for grounded refusal. Correction to an earlier
version of this section, which claimed the hard corpus is what made this visible: it is not. The easy
PostgreSQL corpus already shows mistral:7b at 54% absence coverage against 92-100% for every other
model in the sweep (qwen2.5:0.5b and 3b sit at 12/13). The hard corpus confirmed the family effect; the ordinary corpus had already exposed it,
which is itself the more useful lesson - run the sweep you have before building a harder one.

Note the two failure directions, both caught only by reporting both columns. And read the small-model
case carefully, because the obvious reading is backwards: it is not that qwen2.5:0.5b *answers*
poorly, it is that a 0.5b **verifier** refuses almost everything. Its draft model refused 1/17
absence cases on Blender and produced 0/62 false refusals; the verification pass then added +14
absence cases and **+57 false refusals** on top, ending at 92% (57/62) wrongly refused, and +25 on
PostgreSQL. So the mechanism inverts below a size floor: instead of catching what the model missed,
it rejects nearly everything it is shown. That is a property of the mechanism, not of the model's
willingness to answer, and only the baseline column makes it visible. mistral:7b fails the other way on the absence axis (56% coverage on the
full hard run, 53% as shipped) **while also over-refusing** (17% at n=12 full, 22% at n=9 shipped) -
under symmetric scoring it is not the permissive model an earlier version of this document described,
it is simply weak in both directions. A single-direction score would have rated 0.5b "perfect" on
absence and mistral "perfect" on false-refusal. Both are unusable.

## 6. The limits

- **It measures the model, not retrieval.** The context is held fixed (the correct chunks are handed in);
 retrieval quality is a separate eval. A production failure can come from bad retrieval with this eval
 green.
- **Refusal detection is keyword-based, and since scoring became symmetric it drives both columns.**
  A draft counts as "refused" when it matches a list of refusal phrases. A hedged answer that refuses
  and then supplies an invented answer can match, so absence coverage is an upper bound; and an
  answerable answer that says "the material does not specify the version, but it does say X" can also
  match, so the false-refusal column is an upper bound too. The scoring code is 20 lines; read it
  rather than trusting this sentence.
- **Verifier-judging-generator has its own error bar.** The second pass is the same class of model
 judging the first; it can be wrong (part of the false-refusal is this). An independent, stronger judge
 would tighten it.
- **Model- and corpus-specific.** Every number is for a named model on a named corpus; changing either
 invalidates it. Re-run on change. A startup guard (in our system) fails loudly if the running model is
 not the one the eval measured.
- **Small n on the hard set.** 25 genuinely-silent absence cases in the full run (17 in the published
 subset) is enough to separate models but not to pin a percentage tightly. Grow it before quoting a
 hard number as precise.
- **The floor is a *capable* model, not just a big one.** Below a 7B-class model the verifier collapses
 into refusing everything; but not every 7B works (mistral fails). "Use a 7B+ from a strong family
 (qwen / llama / gemma), verify on your own corpus" is the honest rule, not "use 7B."
