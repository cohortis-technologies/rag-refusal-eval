#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""The grounding-verification approach as a minimal standalone script: nothing but stdlib + an
OpenAI-compatible chat endpoint. This is the mechanism in ~50 lines: draft, then a cheap second call judges whether the material
actually supports the draft; UNSUPPORTED becomes a deterministic refusal. There is no threshold to
tune (it is model-based), which is the property that makes it transfer across corpora.

The pattern is standard, not ours: see Self-RAG's critique tokens (Asai et al., ICLR 2024),
Chain-of-Verification (arXiv:2309.11495), MiniCheck (EMNLP 2024), and the groundedness checks shipped
by Ragas, TruLens, Vectara HHEM and Patronus Lynx. This file exists to make the mechanism readable in
one screen, not to claim it.

Run it against a hosted OpenAI-compatible endpoint or any local ollama model:
  python3 demo_grounding_verify.py                      # Groq llama-3.3-70b (reads .groq_key)
  BASE=http://localhost:11434/v1 MODEL=qwen2.5:7b python3 demo_grounding_verify.py
"""
import json, os, urllib.request

BASE = os.environ.get("BASE", "https://api.groq.com/openai/v1")
MODEL = os.environ.get("MODEL", "llama-3.3-70b-versatile")

def _key():
    k = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY", "")
    kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".groq_key")
    if not k and "groq" in BASE and os.path.exists(kf):
        k = open(kf).read().strip()
    return k.strip()

def chat(system, user):
    body = json.dumps({"model": MODEL, "temperature": 0,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "grounding-verify-demo/1.0"}
    if _key():
        headers["Authorization"] = "Bearer " + _key()
    req = urllib.request.Request(BASE.rstrip("/") + "/chat/completions", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

REFUSAL = "I can't find that in the provided material."
ANSWER_SYS = ("Answer the question using ONLY the material below. If the material does not contain the "
              "answer, reply with EXACTLY: '" + REFUSAL + "' and nothing else. Do not add outside knowledge.")
VERIFY_SYS = ("You are a grounding verifier. Given a QUESTION, the MATERIAL, and a proposed ANSWER, decide "
              "one thing: does the material actually contain the answer to the question? Reply UNSUPPORTED "
              "if the material does not address the question or the answer's core facts are not in it; "
              "reply SUPPORTED if the material contains the answer's main facts (rewording is fine). A pure "
              "refusal is SUPPORTED. Reply with exactly one word: SUPPORTED or UNSUPPORTED.")

def grounded_answer(material, question):
    draft = chat(ANSWER_SYS, "MATERIAL:\n%s\n\nQUESTION: %s" % (material, question))
    verdict = chat(VERIFY_SYS, "QUESTION:\n%s\n\nMATERIAL:\n%s\n\nANSWER:\n%s\n\nOne word:" % (
        question, material, draft))
    # Fail OPEN on an off-format verdict: only a LEADING 'unsupported' token refuses.
    unsupported = verdict.strip().lower().split()[0].strip(".:,").startswith("unsupported") if verdict.strip() else False
    return (REFUSAL, "REFUSED (verifier: UNSUPPORTED)") if unsupported else (draft, "answered (verifier: SUPPORTED)")

if __name__ == "__main__":
    MATERIAL = ("Page title: Watering\nThe fiddle-leaf fig prefers to dry out slightly between waterings. "
                "Water it when the top 2-3 cm of soil is dry, roughly once a week in summer.")
    for q in ["How often should I water a fiddle-leaf fig?",     # in the material -> should answer
              "What temperature should I keep my fiddle-leaf fig at?"]:  # NOT in the material -> should refuse
        ans, why = grounded_answer(MATERIAL, q)
        print("\nQ: %s\n-> [%s]\n   %s" % (q, why, ans.replace("\n", " ")))
