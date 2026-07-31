#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 AND PSF-2.0
"""Adversarial absence corpus. Absence is the liability and the thinnest
category, so this corpus is absence-heavy and deliberately hard, across two openly-licensed domains:

  - SQLite   (documentation dedicated to the public domain, sqlite.org)
  - Python   (standard library; Python docs under the PSF license, docs.python.org/license.html)

A third domain (Redis, 8 absence + 3 answerable cases) existed in the original private run. It is
WITHHELD from this published corpus: license diligence (2026-07-30) showed current redis.io
documentation is CC BY-NC-SA 4.0 (NonCommercial), which this repository cannot honestly
redistribute. Both the full-run numbers (with Redis) and the shipped-subset numbers (this file) are
reported in results/RESULTS.md; the per-case score rows for the withheld cases (ids RD_A*/OK_RD*,
scores only, no excerpt text) remain in results/ for transparency.

Three adversarial shapes, the ones where real users get hurt:
  - adjacent-but-different: the material covers a neighbouring feature; the question asks a distinct one
    the material does NOT contain.
  - wrong-prior: the question is phrased so a strong training prior points to a confident answer.
  - partial: the material addresses PART of the question; the honest answer states only the covered part.

THE HARD DISCIPLINE (this cost a false 50% once): a case is GENUINE ABSENCE only if the material is
truly SILENT on the answer. If the material says "there is no X, use Y", the question is ANSWERABLE
(the grounded answer is "no X, use Y"), NOT absent. Every absence case below carries a `why` field
stating why the material is silent; every case that would tempt a "no X, use Y" answer is classified
near-miss (answerable), not absence. Answerable controls are included so FALSE-REFUSAL is measurable.

Same shape as the other corpora: `c_*` (title, text) chunks + a CASES list, consumed by gate_eval.py.


LICENSING (SPDX-License-Identifier: Apache-2.0 AND PSF-2.0)
  - SQLite chunks: the SQLite documentation is dedicated to the public domain
    (https://www.sqlite.org/copyright.html); no obligations attach. Courtesy provenance:
    excerpts from https://sqlite.org documentation.
  - Python chunks: excerpts from the Python 3 documentation, https://docs.python.org/3/.
    Copyright (c) 2001 Python Software Foundation; All Rights Reserved. Licensed under the
    Python Software Foundation License Version 2 (full text: LICENSES/PSF-2.0.txt and
    https://docs.python.org/3/license.html). Changes: excerpted into evaluation chunks,
    otherwise verbatim.
  - Questions, labels, and why-rationale are original work, Apache-2.0 like the harness.
"""

# ==================== SQLite (public domain) ====================
SQ_DT = "SQLite Datatypes and Type Affinity"
SQ_KEY = "SQLite Keys, rowid, and AUTOINCREMENT"
SQ_PRAGMA = "SQLite PRAGMA and the CLI Shell"
SQ_TXN = "SQLite Transactions and Journal Modes"

c_sq_affinity = (SQ_DT, "SQLite uses dynamic typing. A value has one of five storage classes: NULL, "
    "INTEGER, REAL, TEXT, and BLOB. Columns have a type AFFINITY (TEXT, NUMERIC, INTEGER, REAL, or BLOB) "
    "that influences storage, but any column can hold any storage class. There is no separate BOOLEAN "
    "storage class: booleans are stored as integers 0 (false) and 1 (true). There is no separate DATE or "
    "DATETIME storage class either; date and time values are stored as TEXT, REAL, or INTEGER and "
    "manipulated with the built-in date and time functions.")
c_sq_rowid = (SQ_KEY, "Every ordinary SQLite table (unless WITHOUT ROWID) has a hidden 64-bit signed "
    "integer key called the rowid. A column declared INTEGER PRIMARY KEY becomes an alias for the rowid. "
    "Insert NULL into it and SQLite assigns an unused integer, usually one more than the largest rowid in "
    "use. That is how a table gets an auto-assigned integer id by default, with no extra keyword.")
c_sq_autoinc = (SQ_KEY, "The AUTOINCREMENT keyword, allowed only on an INTEGER PRIMARY KEY column, changes "
    "rowid assignment so a rowid is never reused over the database's lifetime, using the internal "
    "sqlite_sequence table. It has a cost and the documentation recommends against it unless never "
    "reusing a rowid is a real requirement.")
c_sq_fk = (SQ_PRAGMA, "Foreign key constraints are parsed but NOT enforced by default, for backwards "
    "compatibility. Enforcement is turned on per connection with 'PRAGMA foreign_keys = ON;', issued "
    "outside a transaction and not persistent across connections.")
c_sq_shell = (SQ_PRAGMA, "The command-line shell has dot-commands that are not SQL. '.tables' lists tables; "
    "'.schema TABLE' prints the CREATE statement; '.databases' lists the attached database files. "
    "'PRAGMA database_list;' returns the same attachment list as an SQL query.")
c_sq_wal = (SQ_TXN, "The default rollback journal can be replaced with write-ahead logging via 'PRAGMA "
    "journal_mode = WAL;'. In WAL mode readers do not block a writer and a writer does not block readers. "
    "WAL is persistent across connections once set.")
c_sq_txn = (SQ_TXN, "A transaction is started with BEGIN and ended with COMMIT or ROLLBACK. SQLite supports "
    "SAVEPOINT and RELEASE for nested savepoints. By default BEGIN starts a deferred transaction that "
    "locks only on first access.")

# ==================== Python standard library (PSF license) ====================
PY_SEQ = "Python: Lists and Dicts"
PY_TXT = "Python: Strings"
PY_IO = "Python: Files and Exceptions"

c_py_list = (PY_SEQ, "A list is a mutable ordered sequence. list.append(x) adds x to the end; "
    "list.insert(i, x) inserts before index i; a list comprehension like [f(x) for x in xs] builds a new "
    "list from an iterable. len(lst) returns the number of items.")
c_py_dict = (PY_SEQ, "A dict maps keys to values; keys must be hashable. d[k] raises KeyError if k is "
    "missing, while d.get(k, default) returns default instead. Since Python 3.7 dicts preserve insertion "
    "order. d.items() iterates key-value pairs.")
c_py_str = (PY_TXT, "Strings are immutable. s.split(sep) returns a list of substrings; s.strip() removes "
    "leading and trailing whitespace; s.join(iterable) joins strings with s as the separator. An f-string "
    "like f'{x}' interpolates the value of x into the text.")
c_py_file = (PY_IO, "open(path, mode) returns a file object; use it in a 'with open(path) as f:' block so "
    "it closes automatically. f.read() reads the whole file into a string; f.readlines() returns a list of "
    "lines; mode 'w' truncates, 'a' appends.")
c_py_exc = (PY_IO, "A try/except block catches exceptions: 'except ValueError as e:' binds the exception; "
    "an else clause runs if no exception occurred; a finally clause always runs. 'raise' re-raises the "
    "current exception.")

def chunk(pair): return "Page title: %s\n%s" % pair
def ctx(*pairs): return "\n\n---\n\n".join(chunk(p) for p in pairs)

CASES = [
 # ============ GENUINE ABSENCE: SQLite (material silent on the asked feature) ============
 dict(id="SQ_A1", cat="absence", context=ctx(c_sq_rowid, c_sq_autoinc), refuse=True,
      q="How do I make a column auto-generate a UUID as its primary key in SQLite?",
      why="material covers integer rowid/AUTOINCREMENT only; it never mentions UUIDs or randomblob.",
      not_contains=["randomblob", "uuid()", "gen_random_uuid", "lower(hex"]),
 dict(id="SQ_A2", cat="absence", context=ctx(c_sq_wal, c_sq_txn), refuse=True,
      q="How do I set the busy_timeout so writers wait instead of failing with SQLITE_BUSY?",
      why="material covers WAL + transactions; busy_timeout / PRAGMA busy_timeout appears nowhere.",
      not_contains=["pragma busy_timeout", "set busy_timeout", "milliseconds"]),
 dict(id="SQ_A3", cat="absence", context=ctx(c_sq_shell), refuse=True,
      q="Which dot-command exports a table to CSV in the SQLite shell?",
      why="material lists .tables/.schema/.databases; .mode/.output/CSV export are not present.",
      not_contains=[".mode csv", ".output", ".import", ".once"]),
 dict(id="SQ_A4", cat="absence", context=ctx(c_sq_txn), refuse=True,
      q="How do I write a stored procedure in SQLite using CREATE PROCEDURE?",
      why="material covers transactions/savepoints; SQLite stored procedures are not mentioned at all.",
      not_contains=["create procedure", "delimiter", "begin ... end block"]),
 dict(id="SQ_A5", cat="absence", context=ctx(c_sq_affinity, c_sq_shell), refuse=True,
      q="How do I add a full-text search index over a text column in SQLite?",
      why="material covers type affinity + the shell; FTS5 / full-text search is absent.",
      not_contains=["fts5", "create virtual table", "using fts", "match"]),
 dict(id="SQ_A6", cat="absence", context=ctx(c_sq_txn, c_sq_wal), refuse=True,
      q="How do I run VACUUM to reclaim free space and defragment an SQLite database?",
      why="material covers transactions/journal modes; VACUUM is not mentioned.",
      not_contains=["vacuum", "auto_vacuum", "pragma incremental_vacuum"]),
 dict(id="SQ_A7", cat="absence", context=ctx(c_sq_affinity, c_sq_rowid), refuse=True,
      q="How do I encrypt an SQLite database file at rest?",
      why="material covers datatypes + keys; encryption / SEE / SQLCipher is not present.",
      not_contains=["sqlcipher", "pragma key", "see extension", "encrypt"]),
 dict(id="SQ_A8", cat="absence", context=ctx(c_sq_rowid, c_sq_txn), refuse=True,
      q="How do I create an index on a column to speed up queries in SQLite?",
      why="material covers primary keys/rowid and transactions; CREATE INDEX / secondary indexes are absent.",
      not_contains=["create index", "create unique index", "on table("]),
 dict(id="SQ_A9", cat="absence", context=ctx(c_sq_txn), refuse=True,
      q="How do I create a trigger that runs after an INSERT in SQLite?",
      why="material covers transactions/savepoints; triggers (CREATE TRIGGER) are not mentioned.",
      not_contains=["create trigger", "after insert", "for each row"]),

 # ============ GENUINE ABSENCE: Python standard library (material silent) ============
 dict(id="PY_A1", cat="absence", context=ctx(c_py_list, c_py_dict, c_py_str), refuse=True,
      q="How do I make an HTTP GET request in Python with the requests library?",
      why="material covers list/dict/str only; no networking, requests, or urllib anywhere.",
      not_contains=["requests.get", "import requests", "urllib.request", "http.client"]),
 dict(id="PY_A2", cat="absence", context=ctx(c_py_file, c_py_exc), refuse=True,
      q="How do I run tasks concurrently in Python using asyncio and await?",
      why="material covers files + exceptions; asyncio / async / await is absent.",
      not_contains=["asyncio", "async def", "await ", "event loop"]),
 dict(id="PY_A3", cat="absence", context=ctx(c_py_list, c_py_str), refuse=True,
      q="How do I parse command-line arguments in Python with argparse?",
      why="material covers lists + strings; argparse / sys.argv is not mentioned.",
      not_contains=["argparse", "add_argument", "argumentparser", "sys.argv"]),
 dict(id="PY_A4", cat="absence", context=ctx(c_py_dict, c_py_file), refuse=True,
      q="How do I serialize a dictionary to a JSON string in Python with the json module?",
      why="material covers dicts + files; the json module (dumps/loads) is absent.",
      not_contains=["json.dumps", "json.loads", "import json"]),
 dict(id="PY_A5", cat="absence", context=ctx(c_py_list, c_py_dict), refuse=True,
      q="How do I define a dataclass in Python with the @dataclass decorator?",
      why="material covers list/dict; dataclasses / decorators are not present.",
      not_contains=["@dataclass", "from dataclasses", "field("]),
 dict(id="PY_A6", cat="absence", context=ctx(c_py_str, c_py_exc), refuse=True,
      q="How do I match text against a regular expression in Python with the re module?",
      why="material covers strings (split/strip/join) + exceptions; the re module is absent.",
      not_contains=["re.match", "re.search", "import re", "re.compile"]),
 dict(id="PY_A7", cat="absence", context=ctx(c_py_file, c_py_list), refuse=True,
      q="How do I create an isolated virtual environment in Python with venv?",
      why="material covers files + lists; venv / pip / environments are absent.",
      not_contains=["python -m venv", "virtualenv", "pip install", "activate"]),
 dict(id="PY_A8", cat="absence", context=ctx(c_py_dict, c_py_str), refuse=True,
      q="How do I measure how long a small snippet takes to run in Python with timeit?",
      why="material covers dict + str; timeit / time.perf_counter are absent.",
      not_contains=["timeit", "perf_counter", "time.time"]),


 # ============ NEAR-MISS (ANSWERABLE): material states the absence-of-feature or the equivalent ============
 # These would be a false absence if marked refuse: the grounded answer is "there is no X" / "use Y".
 dict(id="NM1", cat="near-miss", context=ctx(c_sq_affinity),
      q="What is the value range of the BOOLEAN type in SQLite?",
      any_of=["no separate", "integer", "0", "1"], not_contains=["-128", "stored as a bit"]),
 dict(id="NM2", cat="near-miss", context=ctx(c_sq_shell),
      q="What is the SQLite equivalent of MySQL's SHOW DATABASES; command?",
      any_of=[".databases", "database_list"], not_contains=["show databases", "information_schema"]),
 dict(id="NM3", cat="near-miss", context=ctx(c_sq_autoinc, c_sq_rowid),
      q="What is the SERIAL type in SQLite and how do I use it like in PostgreSQL?",
      any_of=["integer primary key", "rowid", "no serial", "does not have"], not_contains=["bigserial", "create a sequence"]),
 dict(id="NM4", cat="near-miss", context=ctx(c_py_dict),
      q="What Python exception does d[k] raise for a missing key, and how do I avoid it?",
      any_of=["keyerror", ".get"], not_contains=["indexerror", "returns none silently by default"]),

 # ============ ANSWERABLE CONTROLS (measure FALSE-REFUSAL; these MUST be answered) ============
 dict(id="OK_SQ1", cat="extractive", context=ctx(c_sq_rowid),
      q="How does an SQLite table get an auto-assigned integer id by default?",
      any_of=["integer primary key", "rowid", "alias"], not_contains=[]),
 dict(id="OK_SQ2", cat="extractive", context=ctx(c_sq_fk),
      q="Are foreign key constraints enforced by default in SQLite?",
      any_of=["not enforced", "off by default", "pragma foreign_keys"], not_contains=[]),
 dict(id="OK_PY1", cat="extractive", context=ctx(c_py_list),
      q="How do I add an item to the end of a Python list?", any_of=["append"], not_contains=[]),
 dict(id="OK_PY2", cat="extractive", context=ctx(c_py_dict),
      q="How do I look up a dict key without raising if it is missing?", any_of=[".get"], not_contains=[]),
 dict(id="OK_PY3", cat="extractive", context=ctx(c_py_file),
      q="How do I open a file so it closes automatically in Python?", any_of=["with open", "with-statement", "with statement"], not_contains=[]),
]
