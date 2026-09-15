## Phase 0 — pip install kokoro fails building spacy/blis from source

**Problem:** `pip install kokoro ...` on the system Python (3.13) failed while
building `misaki[en]`'s `spacy` dependency. Pip's resolver backtracked to
`spacy==4.0.0.dev3` (a pre-release), which needed `thinc==9.0.0`, which needed
to build `blis` from source — and that build failed on a real Cython/numpy
version mismatch in blis's .pyx files.

**Diagnosis:** No prebuilt wheels exist for spacy/thinc/blis for Python 3.13
in the version range the resolver settled on, forcing a source build that
this machine's toolchain couldn't complete. Not a Kokoro-specific bug — a
long-standing spacy/thinc/blis packaging gap on very new Python versions.

**Fix:** Created the project venv on Python 3.10 (`py -3.10 -m venv venv`)
instead of system 3.13. Reinstalled into the clean venv — everything resolved
to prebuilt wheels, zero source compilation.

**Why it matters:** Phase 7's Dockerfile targets `python:3.11-slim`. Building
locally on 3.10 (not 3.13) means dev and prod are both on mature-wheel Python
versions — a real gap worth a one-line note when Phase 7 comes up, but not
the kind of Python-version mismatch that causes "works locally, breaks in
Docker" surprises.

## Phase 0 — Kokoro under-emphasizes leading proper nouns at normal volume

**Problem:** In `verify_stack.py`'s test output, "Herald" (the first word of
the test line) was inaudible at normal laptop-speaker volume, while the rest
of the line played clearly.

**Diagnosis:** Checked the waveform directly (`dev_checks/debug_audio.py`) —
peak amplitude for "Herald" was ~0.23 vs ~0.36 for the rest of the line. Real
signal, not silence — confirmed audible at higher volume/headphones. Likely
natural under-emphasis on an unusual proper noun the 82M-parameter model has
little training data for, not a synthesis bug.

**Fix:** None needed for Phase 0 — not a bug. Noting for Phase 3: if real
generated briefings ever open with an unusual proper noun (unlikely — Herald's
persona greets first, states the time next), keep an ear out for the same
soft-lead-word pattern.

**Why it matters:** Distinguishing "quiet but real" from "actually silent"
before treating something as a bug — the debug_checks approach (inspecting
the waveform directly instead of guessing from ear) is the same instinct
worth applying to any future audio weirdness in this project.
