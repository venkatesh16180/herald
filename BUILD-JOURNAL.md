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

## Phase 1 — pip self-locks its own .exe mid-upgrade on Windows

**Problem:** `pip install pip-tools` triggered a pip self-upgrade (needed
pip>=22.2, had 22.0.4) partway through, which failed with
`[WinError 5] Access is denied` while uninstalling the old pip.exe.

**Diagnosis:** Windows won't let a running process delete or overwrite its
own executable file. `pip.exe` trying to replace itself via `pip install`
hits that lock every time — this isn't project-specific, it's a general
Windows/pip interaction.

**Fix:** Use `python -m pip install --upgrade pip` instead of `pip install
--upgrade pip` — invoking pip as a module through python.exe (not the
locked pip.exe) sidesteps the self-lock. Also had to clean up a stray
`~ip`/`~ip-22.0.4.dist-info` folder left behind by the interrupted
uninstall (`Remove-Item -Recurse -Force venv\Lib\site-packages\~ip*`).

**Why it matters:** `python -m pip` is generally the safer invocation on
Windows for any pip self-upgrade going forward, not just this one time.

## Phase 1 — Adopted pip-compile / pip-sync for dependency management

**Problem:** N/A — proactive change, not a bug fix. requirements.txt had been
an empty placeholder since Phase 0's scaffold, drifting from what was
actually installed.

**Fix:** Introduced pip-tools. requirements.in now lists only direct
dependencies (kokoro, soundfile, ollama, requests, feedparser, plus
en_core_web_sm pinned via its GitHub release URL since it's not a normal
PyPI package). pip-compile generates a fully pinned requirements.txt;
pip-sync keeps the venv matching it exactly — including removing anything
installed outside that contract, which is how the en_core_web_sm churn
surfaced and got fixed properly.

**Why it matters:** CI (Phase 6) and Docker (Phase 7) still just run
`pip install -r requirements.txt` — this is additive, not a rework. Going
forward, every new package goes into requirements.in first, then
pip-compile + pip-sync, never a bare pip install.

## Phase 2 — Verifying a bounded retry loop requires forcing the failure case

**Problem:** Two natural-language test inputs (a 2-headline draft, then a
20-headline draft) both composed well under the 220-word budget on the first
pass. attempts stayed at 1 both times \u2014 the retry path was never actually
exercised, only assumed to work because the wiring looked right.

**Fix:** Mocked ollama.chat via unittest.mock.patch to return a fixed
300-word reply regardless of input. Since the mock never varies, this
proves two things a natural-language test can't: that route_on_length
correctly sends an over-budget draft to tighten, and that MAX_ATTEMPTS
actually bounds the loop even when the content never improves (attempts
landed at exactly 2, not more, not stuck at 1).

**Why it matters:** A happy-path test that never enters an error/retry
branch tells you nothing about that branch. This same mock-the-LLM-call
pattern is exactly what Phase 6's CI test suite needs to run green with no
Ollama server available \u2014 this was effectively a preview of it.

## Phase 3 — Leading silence in synthesized audio, partially mitigated

**Problem:** Kokoro's concatenated output had ~300ms of true digital silence
(measured, not perceived -- peak amplitude ~0.00003) before any real speech,
making playback sound like it hadn't started.

**Diagnosis:** Confirmed via direct waveform inspection, not by ear. Trimming
the silence down too aggressively (50ms pad) caused the actual first word to
sound clipped instead -- likely the playback device's own anti-pop fade-in
ramp landing on top of real audio rather than silence.

**Fix:** Amplitude-threshold trim in speak.py, landed on a 250ms pad as a
middle ground. Reduces the original ~300ms gap without triggering the
clipped-onset problem at 50ms, but does not eliminate the perceptual issue
entirely -- accepted as a known minor limitation rather than pursued further.

**Why it matters:** Not every audio artifact is worth chasing to zero,
especially on CPU-only TTS. Measuring the waveform directly (not trusting
ear alone) was still worthwhile -- it's what caught the 50ms overcorrection
before it shipped as "fixed."

## Phase 3 — Leading-silence trim has a narrow, imperfect working range

**Problem:** Kokoro's output had ~300ms of true digital silence before real
speech (confirmed via waveform, peak ~0.00003). An amplitude-threshold trim
was added to speak.py to cut it.

**Diagnosis:** Tested pad_ms at 0, 50, 150, and 500. Found a real bug in the
trim math, not just a tuning question: `start = max(0, crossing_index -
pad_samples)` clamps to 0 whenever pad_ms exceeds the actual gap length --
so pad_ms=500 against a ~300ms gap silently did nothing, reproducing the
original problem. pad_ms=0 clips directly into the first word's onset
consonant. Every value tried in between (50/150ms) was an audible partial
improvement, never fully clean.

**Fix:** Deferred, not resolved. Shipping with pad_ms=150 as the least-bad
compromise found. Documented here rather than claimed fixed.

**Why it matters:** Not every audio artifact is worth chasing to zero,
especially on CPU-only TTS with a small model. The real value here was
catching that "more padding" doesn't monotonically mean "safer" --
worth remembering before reaching for this same trim-by-threshold pattern
on a future project without checking the boundary math first.

## Phase 5 — BriefingRequest.city accepted but not wired through

**Note, not a bug:** BriefingRequest.city validates and is accepted by
POST /briefing/generate, but generate_briefing() doesn't actually use it --
get_weather() always reads config.CITY regardless of what's passed. Left
as-is deliberately for this phase; wiring it through is a small,
well-understood follow-up whenever there's a reason to actually override
city per-request.
