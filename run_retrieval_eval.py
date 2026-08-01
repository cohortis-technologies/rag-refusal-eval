#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
Retrieval eval for the local embedding decision. For each candidate embedding model, does the
CORRECT chunk make top-k for each corpus question? Reports recall@1, recall@3, dimensions, embed
latency, and an analytical index size. Embeddings via the running ollama HTTP API. This scores
RETRIEVAL (which chunk comes back), complementary to run_eval.py which scores GENERATION.

Caveat (same as run_eval.py): the corpus is three documents I wrote and the questions I wrote, so it
runs easier than a real operator's messy materials. n=17 retrieval cases -> wide error bars; treat
small recall gaps as noise. Replace the corpus with a real operator's docs at the first opportunity.
"""
import json, sys, time, math, urllib.request, os

# Derive the embed endpoint from OLLAMA_URL when OLLAMA_EMBED_URL is not set, so a single
# variable points BOTH the chat and embed calls at the same server. Setting only OLLAMA_URL
# used to leave embeddings pointing at localhost:11434, silently splitting one run across two
# servers (or failing mid-run after the model pull).
_RAW_EMBED = (os.environ.get("OLLAMA_EMBED_URL")
              or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
# Same either-form tolerance as run_eval.py: a base URL, a chat endpoint, or an embed endpoint.
if _RAW_EMBED.endswith("/api/embed"):
    OLLAMA = _RAW_EMBED
elif "/api/" in _RAW_EMBED:
    OLLAMA = _RAW_EMBED.rsplit("/api/", 1)[0] + "/api/embed"
else:
    OLLAMA = _RAW_EMBED + "/api/embed"

# Raw chunk text as CourseContentIngestor stores it (the "Page title:" prefix is added at retrieval
# time, not embedded), keyed by a short id.
CHUNKS = {
 "software": "You will need Blender 4.2 LTS, which is free to download. A graphics tablet is recommended but not required; you can complete every lesson with a mouse.",
 "dates":    "Cohort 4 runs from March 10 to May 1. Enrollment closes on March 3, and the cohort starts on March 10.",
 "critique": "A new lesson is posted every Monday. Live critiques are held every Wednesday at 6:00pm Eastern in the voice channel.",
 "final":    "Week 8: Portfolio piece. The final portfolio piece is due at the end of Week 8. To complete the course you must submit at least six of the eight weekly exercises plus the final piece.",
 "mirror":   "Start from a single default cube. Add a Mirror modifier so both halves of the character stay symmetrical while you work.",
 "ratio":    "For a stylized character, keep the head roughly one seventh of the total body height. Do not add small details yet; blocking is only about proportion.",
 "feedback": "Post your work in the #critique-corner channel. The instructor reviews every submission within 48 hours.",
 "office":   "Office hours are Fridays from 3:00 to 4:00pm Eastern in the voice channel. The instructor personally answers questions in the #ask-anything channel.",
 "refund":   "You can get a full refund within 14 days of enrollment, no questions asked. After 14 days, enrollment is non-refundable.",
}

# (question, gold chunk ids). A separate small course-admin corpus (NOT the run_eval.py cases);
# recall@k = at least one gold in top-k.
QUESTIONS = [
 ("What version of Blender do I need for this course?", ["software"]),
 ("When are office hours?", ["office"]),
 ("How many days do I have to get a full refund?", ["refund"]),
 ("How big should the head be relative to the body for a stylized character?", ["ratio"]),
 ("What day and time are the live critiques?", ["critique"]),
 ("I just finished my Week 1 blockout. Where do I post it, and how long until I get feedback?", ["feedback"]),
 ("When does the cohort start, and what software do I need ready before then?", ["dates", "software"]),
 ("What is the last week of the course about, and when is the final due?", ["final"]),
 ("How do I keep my model symmetrical while blocking, and how detailed should it be at this stage?", ["mirror", "ratio"]),
 ("When is the live critique, and which document does that come from?", ["critique"]),
 ("Where should I post my work for feedback, and what is the source document?", ["feedback"]),
 ("What is the head-to-body ratio, and which lesson does it come from?", ["ratio"]),
 ("What is the refund window, and cite the exact title of the document?", ["refund"]),
 ("When are office hours?", ["office"]),
 ("What is the head-to-body ratio for a stylized character?", ["ratio"]),
 ("What exact date does the cohort START?", ["dates"]),
 ("When are OFFICE HOURS, specifically? Not the critique, the office hours.", ["office"]),
]

def embed(model, text):
    body = json.dumps({"model": model, "input": text}).encode()
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    ms = (time.time() - t0) * 1000
    v = d.get("embeddings", [[]])[0]
    return v, ms

def cosine(a, b):
    # strict=True: both vectors always come from the same embedding model, so a length mismatch
    # means something upstream is wrong and should fail loudly rather than silently truncate.
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

def run(models):
    print("model                        dim  recall@1  recall@3  embed_ms  idx_MB/1k_chunks")
    for model in models:
        try:
            chunk_vecs = {}; lat = []
            for cid, text in CHUNKS.items():
                v, ms = embed(model, text); chunk_vecs[cid] = v; lat.append(ms)
            dim = len(next(iter(chunk_vecs.values())))
            r1 = r3 = 0
            for q, gold in QUESTIONS:
                qv, ms = embed(model, q); lat.append(ms)
                ranked = sorted(CHUNKS.keys(), key=lambda c: cosine(qv, chunk_vecs[c]), reverse=True)
                if ranked[0] in gold: r1 += 1
                if any(g in ranked[:3] for g in gold): r3 += 1
            n = len(QUESTIONS)
            # HNSW index size scales ~ rows * dim * 4 bytes * ~1.5 (graph overhead).
            idx_mb = 1000 * dim * 4 * 1.5 / (1024 * 1024)
            print("%-28s %4d  %d/%d %3.0f%%  %d/%d %3.0f%%  %6.0f  %5.1f" % (
                model, dim, r1, n, 100*r1/n, r3, n, 100*r3/n, sum(lat)/len(lat), idx_mb))
        except Exception as e:
            print("%-28s ERROR %s" % (model, e))

if __name__ == "__main__":
    run(sys.argv[1:] or ["nomic-embed-text", "mxbai-embed-large", "snowflake-arctic-embed2", "bge-m3"])
