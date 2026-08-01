# SPDX-License-Identifier: Apache-2.0
"""Measure two mechanisms that take the refusal decision away from the model, on the
real-docs corpus, reporting BOTH directions (absence coverage AND false-refusal on answerable
questions).

  (a) Retrieval-confidence gate: embed the question, take the top-1 cosine similarity against the
      course chunk index (nomic-embed-text, the production embedder). If it is below a threshold,
      refuse deterministically without calling the chat model.
  (b) Verification pass: draft the answer with the chat model, then a second cheap call asks whether
      the retrieved context actually supports the draft; UNSUPPORTED -> refuse.

Ground truth: absence cases SHOULD be refused; every other category (extractive, synthesis, citation,
near-miss, injection) is answerable and should NOT be refused. We report, for each mechanism, absence
coverage (good = high) and false-refusal rate on answerable questions (good = low = 0), plus a
threshold sweep for the gate so the tradeoff is visible.

Usage: python3 gate_eval.py [corpus_module] [draft_model]
  corpus_module default corpus_blender_real ; draft_model default qwen2.5:7b
Writes a per-case JSON next to this file: gate_rows_<corpus>_<model>.json
"""

import importlib
import json
import os
import re
import sys

import run_eval  # SYSTEM, build_user, call_model, score, guard_output, ABSENCE_REFUSAL, neutralize/sanitize
from run_retrieval_eval import cosine, embed

EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
ANSWERABLE = {"extractive", "synthesis", "citation", "near-miss", "injection"}  # gate should PASS
ABSENT = {"absence"}  # gate should REFUSE

# v2 verifier: judges whether the MATERIAL ADDRESSES THE QUESTION and contains the answer's core facts,
# tolerating rewording. Over-strict "any new fact -> UNSUPPORTED" wrongly refused correct grounded
# answers that merely rephrase; keying on core claims + on-topic-ness fixes that without letting the
# invented-procedure absence answers through (their core procedure is simply not in the material).
VERIFY_SYSTEM = os.environ.get("VERIFY_PROMPT", "v2")
_VERIFY_SYSTEMS = {
    "v1": (
        "You are a strict grounding verifier for a study assistant. You are given COURSE MATERIAL and a "
        "proposed ANSWER. Decide whether EVERY specific factual claim in the answer (steps, setting names, "
        "menu paths, values, version numbers, hardware specs) is directly stated in or entailed by the "
        "course material. If the answer introduces ANY specific fact that is not present in the material, "
        "reply UNSUPPORTED. If the answer only says it cannot find the information (a refusal), reply "
        "SUPPORTED. Reply with exactly one word: SUPPORTED or UNSUPPORTED."
    ),
    "v2": (
        "You are a grounding verifier for a study assistant. You are given a QUESTION, the COURSE MATERIAL "
        "retrieved for it, and a proposed ANSWER. Decide one thing: does the course material actually "
        "contain the answer to this question? Reply UNSUPPORTED if the material does not address the "
        "question, or if the answer's core steps/values/facts are not found in the material (the answer is "
        "drawn from outside knowledge). Reply SUPPORTED if the material contains the answer's main facts, "
        "even if the answer rewords, reorders, or lightly elaborates them. Ignore differences of phrasing. "
        "A pure refusal to answer is SUPPORTED. Reply with exactly one word: SUPPORTED or UNSUPPORTED."
    ),
}


def verify_user(context, draft, question):
    # Reuse the same sanitiser/neutraliser the drafting path uses, so an injection in the material
    # cannot hijack the verifier either.
    safe_ctx = run_eval.neutralize_injections(run_eval.sanitize_context(context))
    return "QUESTION:\n%s\n\nCOURSE MATERIAL:\n%s\n\nPROPOSED ANSWER:\n%s\n\nOne word (SUPPORTED or UNSUPPORTED):" % (
        question, safe_ctx, draft)


def load_chunks(corpus):
    # Every c_* module global is a (title, text) chunk; embed the body text (what production ingests).
    chunks = {}
    for name, val in vars(corpus).items():
        if name.startswith("c_") and isinstance(val, tuple) and len(val) == 2:
            chunks[name] = val[1]
    return chunks


def is_refusal(text):
    tl = text.lower()
    return any(p in tl for p in run_eval.REFUSAL)


def main():
    # Tolerate the near-certain mistake: shell tab-completion appends .py, and importing
    # "corpus_x.py" produced a six-frame importlib traceback instead of saying what was wrong.
    corpus_name = (sys.argv[1] if len(sys.argv) > 1 else "corpus_blender_real").removesuffix(".py")
    draft_model = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5:7b"
    try:
        corpus = importlib.import_module(corpus_name)
    except ModuleNotFoundError:
        sys.exit("unknown corpus %r; expected one of: corpus_blender_real, corpus_transfer, "
                 "corpus_adversarial_absence" % corpus_name)
    cases = corpus.CASES
    chunks = load_chunks(corpus)

    print("### GATE + VERIFY eval  corpus=%s  n=%d  chunks=%d  embed=%s  draft=%s ###"
          % (corpus_name, len(cases), len(chunks), EMBED_MODEL, draft_model))

    # 1) Embed the chunk index once, for the retrieval-gate arm only. This needs a LOCAL embedding
    # endpoint even when the chat model is hosted. Set GATE_ARM=0 to skip it; the verification-pass
    # numbers (the headline ones) do not depend on retrieval at all, because each case carries its
    # own fixed context.
    gate_arm = os.environ.get("GATE_ARM", "1") != "0"
    chunk_vecs = {}
    if gate_arm and not chunks:
        print("WARN: corpus exposes no c_* chunks; skipping the retrieval-gate arm.")
        gate_arm = False
    if gate_arm:
        try:
            # Probe first, so an unreachable endpoint is reported as such rather than surfacing
            # later as an all-zero similarity column that looks like data.
            embed(EMBED_MODEL, "probe")
            chunk_vecs = {cid: embed(EMBED_MODEL, txt)[0] for cid, txt in chunks.items()}
        except Exception as e:
            print("WARN: embedding endpoint unavailable (%s); skipping the retrieval-gate arm. "
                  "Verification-pass numbers are unaffected." % str(e)[:100])
            gate_arm = False

    rows = []
    for c in cases:
        cat = c["cat"]
        answerable = cat != "absence"  # documented rule; ANSWERABLE stays as the category whitelist
        # 2) Retrieval-confidence signal: top-1 cosine over the whole chunk index.
        if gate_arm:
            qv = embed(EMBED_MODEL, c["q"])[0]
            sims = sorted((cosine(qv, v) for v in chunk_vecs.values()), reverse=True)
            max_sim = sims[0] if sims else 0.0
            top3 = sum(sims[:3]) / min(3, len(sims)) if sims else 0.0
        else:
            max_sim = top3 = 0.0
        # 3) Draft with the chat model (same path as production /ask).
        draft, _, _, _ = run_eval.call_model(draft_model, run_eval.SYSTEM, run_eval.build_user(c))
        draft = run_eval.guard_output(draft)  # production also runs the truncation guard
        draft_refused = is_refusal(draft)
        draft_ok, _ = run_eval.score(c, draft)
        # 4) Verification pass.
        verdict, _, _, _ = run_eval.call_model(
            draft_model, _VERIFY_SYSTEMS[VERIFY_SYSTEM], verify_user(c["context"], draft, c["q"]))
        # Mirror production GroundingVerifier.isUnsupported: refuse only on a LEADING "unsupported" token
        # (fail-open on verbose/off-format replies), not a substring anywhere.
        first_token = re.split(r"[^a-z]+", verdict.strip().lower(), maxsplit=1)[0] if verdict.strip() else ""
        unsupported = first_token == "unsupported"
        rows.append(dict(id=c["id"], cat=cat, answerable=answerable, max_sim=round(max_sim, 4),
                         top3=round(top3, 4), draft_refused=draft_refused, draft_ok=draft_ok,
                         verify_unsupported=unsupported))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "gate_rows_%s_%s.json" % (corpus_name, draft_model.replace(":", "-")))
    json.dump(rows, open(out, "w"), indent=1)
    report(rows, gate_arm=gate_arm)
    print("\nrows -> %s" % out)


def report(rows, gate_arm=True):
    absent = [r for r in rows if not r["answerable"]]
    answ = [r for r in rows if r["answerable"]]
    na, nans = len(absent), len(answ)
    if not na or not nans:
        print("WARNING: this corpus has %d absence and %d answerable cases. A rate needs both "
              "directions; refusing to print percentages for an empty side." % (na, nans))

    if not gate_arm or not na or not nans:
        print("\n-- (a) RETRIEVAL-CONFIDENCE GATE: SKIPPED (no embedding endpoint, GATE_ARM=0, "
              "or a corpus with an empty side) --")
        return _verify_report(rows, absent, answ, na, nans)

    print("\n-- (a) RETRIEVAL-CONFIDENCE GATE: sweep top-1 cosine threshold --")
    print("thresh | absence refused (coverage) | answerable refused (FALSE-refusal)")
    grid = [round(x / 100, 2) for x in range(40, 86, 5)]
    for t in grid:
        cov = sum(1 for r in absent if r["max_sim"] < t)
        fr = sum(1 for r in answ if r["max_sim"] < t)
        print("  %.2f  |   %2d/%d  (%3.0f%%)            |   %2d/%d  (%3.0f%%)"
              % (t, cov, na, 100 * cov / na, fr, nans, 100 * fr / nans))
    # separation summary
    ab_max = max((r["max_sim"] for r in absent), default=0)
    an_min = min((r["max_sim"] for r in answ), default=0)
    print("  absence top-1 sim range: [%.3f .. %.3f]; answerable: [%.3f .. %.3f]"
          % (min((r["max_sim"] for r in absent), default=0), ab_max,
             an_min, max((r["max_sim"] for r in answ), default=0)))
    print("  clean-separation threshold exists? %s (absence_max %.3f < answerable_min %.3f)"
          % (ab_max < an_min, ab_max, an_min))

    return _verify_report(rows, absent, answ, na, nans)


def _verify_report(rows, absent, answ, na, nans):
    print("\n-- (b) VERIFICATION PASS: draft, then SUPPORTED/UNSUPPORTED check --")
    # SYMMETRIC SCORING. A refusal is a refusal whichever layer produced it: the user sees the same
    # thing. Scoring coverage on (draft OR verifier) while scoring false-refusal on the verifier alone
    # would flatter the system in BOTH columns at once - it credits draft refusals as coverage and
    # hides them as false refusals. An earlier version of this harness did exactly that; under it
    # mistral:7b appeared to have 0% false-refusal when it was really refusing 2 of 9 answerable
    # questions at draft time.
    cov = sum(1 for r in absent if r["draft_refused"] or r["verify_unsupported"])
    fr = sum(1 for r in answ if r["draft_refused"] or r["verify_unsupported"])
    pc = lambda x, n: ("%3.0f%%" % (100.0 * x / n)) if n else " n/a"
    print("  absence coverage (refused): %2d/%d (%s)" % (cov, na, pc(cov, na)))
    print("  answerable FALSE-refusal:   %2d/%d (%s)" % (fr, nans, pc(fr, nans)))
    # Decomposition, so the asymmetry can never hide again.
    fr_draft = sum(1 for r in answ if r["draft_refused"])
    fr_ver = sum(1 for r in answ if r["verify_unsupported"] and not r["draft_refused"])
    print("     of which: model refused at draft %d, verifier added %d" % (fr_draft, fr_ver))
    # verifier-only contribution (beyond what the model already refused)
    caught = sum(1 for r in absent if not r["draft_refused"] and r["verify_unsupported"])
    missed = [r["id"] for r in absent if not r["draft_refused"] and not r["verify_unsupported"]]
    print("  verifier caught %d absence answers the model did NOT refuse; still-missed: %s"
          % (caught, missed or "none"))
    fr_ids = [r["id"] for r in answ if r["verify_unsupported"]]
    print("  answerable cases the verifier wrongly flagged: %s" % (fr_ids or "none"))

    # THE BASELINE THAT DECIDES WHETHER THE MECHANISM IS WORTH ANYTHING. Publish it next to every
    # coverage number: if the model already refuses every absence case unaided, the verification pass
    # contributed nothing on this corpus and the coverage figure is a property of the model.
    draft_ref = sum(1 for r in absent if r["draft_refused"])
    draft_fr = sum(1 for r in answ if r["draft_refused"])
    print("\n  BASELINE, no mechanism (draft alone): absence %d/%d (%s), false-refusal %d/%d (%s)"
          % (draft_ref, na, pc(draft_ref, na), draft_fr, nans, pc(draft_fr, nans)))
    print("  MARGINAL contribution of the verification pass: %+d absence cases, %+d false refusals"
          % (cov - draft_ref, fr - draft_fr))


if __name__ == "__main__":
    main()
