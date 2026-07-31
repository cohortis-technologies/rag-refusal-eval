# Corpus licensing and attribution

The harness code is Apache-2.0 (root `LICENSE`; SPDX headers per file). The corpus files contain
short excerpts (verbatim-or-lightly-condensed, a few sentences to a paragraph per chunk) from
openly-licensed documentation, plus our own questions, labels, and rationale. Each corpus file
carries its required notices in its own header; this file is the manifest. Every license statement
below was verified against the project's own license/copyright page on 2026-07-30.

| corpus file | source | license (verified URL) | what compliance requires, and where it is done |
|---|---|---|---|
| `corpus_blender_real.py` | Blender Manual | CC-BY-SA 4.0 "or any later version" (docs.blender.org/manual/en/latest/copyright.html) | Attribution to the **Blender Documentation Team** with a hyperlink (the wording the copyright page requests), license notice + URI, modification statement, per-chunk source pages in `PAGES`. The file itself is `SPDX: CC-BY-SA-4.0`. Full license text: `LICENSES/CC-BY-SA-4.0.txt`. |
| `corpus_transfer.py` | PostgreSQL documentation | PostgreSQL License; the docs' Legal Notice covers "this software and its documentation" (postgresql.org/docs/current/legalnotice.html) | The grant requires the copyright notice + permission paragraph + both disclaimer paragraphs to "appear in all copies": reproduced verbatim in the file header and in `LICENSES/PostgreSQL-legal-notice.txt`. No share-alike. |
| `corpus_adversarial_absence.py` (SQLite chunks) | SQLite documentation | Public domain, explicit dedication covering code AND documentation (sqlite.org/copyright.html) | Nothing required; courtesy provenance note in the file header. |
| `corpus_adversarial_absence.py` (Python chunks) | Python 3 documentation | PSF License Version 2; doc code examples additionally 0BSD since Python 3.8.6 (docs.python.org/3/license.html) | PSF copyright notice + license identification + change summary in the file header; full text in `LICENSES/PSF-2.0.txt`. |

## The withheld domain (Redis)

The original private run had a third adversarial domain, Redis (8 absence + 3 answerable cases).
It is **not in this repository**. License diligence (2026-07-30) found that the current redis.io
documentation is **CC BY-NC-SA 4.0** (per the LICENSE of github.com/redis/docs, the source repo of
the docs site), i.e. NonCommercial, and redis.io's trademark policy separately restricts copying
docs content to non-commercial use. This project is published by a commercial company, so we do not
redistribute those excerpts. The per-case score rows (ids `RD_A*` / `OK_RD*`, no document text) stay
in `results/` so the full-run aggregates remain checkable. If the domain is ever restored, the
compliant path is rebuilding the chunks from the legacy `github.com/redis/redis-doc` repository,
whose content is plain CC BY-SA 4.0.

## Share-alike scope (CC-BY-SA)

Per the CC BY-SA 4.0 legal code (sections 1(a), 2(a)(1), 3(b)) and Creative Commons' own ShareAlike
interpretation page: share-alike binds **adapted material**, not works merely aggregated in a
collection. The Blender corpus file is marked CC-BY-SA-4.0 (lowest-risk reading, and costless); the
harness code and the other files are separate works in a collection and stay under their own
licenses. Excerpts are kept verbatim within chunks; do not splice original prose into a chunk, which
would make the adaptation reading unavoidable.

## Questions and labels

The questions, answerable/absence labels, `why`-silent rationale, and scoring checks are original
work. In the CC-BY-SA corpus file they are distributed under CC-BY-SA 4.0 with the rest of the file;
elsewhere they are Apache-2.0 like the harness.
