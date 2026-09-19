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
pass. attempts stayed at 1 both times — the retry path was never actually
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
Ollama server available — this was effectively a preview of it.

## Phase 3 — Leading silence in synthesized audio, partially mitigated

**Problem:** Kokoro's concatenated output had ~300ms of true digital silence
(measured, not perceived — peak amplitude ~0.00003) before any real speech,
making playback sound like it hadn't started.

**Diagnosis:** Confirmed via direct waveform inspection, not by ear.
Tested pad_ms at 0, 50, 150, and 500 in speak.py's amplitude-threshold trim.
Found a real bug in the trim math along the way, not just a tuning
question: `start = max(0, crossing_index - pad_samples)` clamps to 0
whenever pad_ms exceeds the actual gap length — so pad_ms=500 against a
~300ms gap silently did nothing, reproducing the original problem.
pad_ms=0 clipped directly into the first word's onset consonant. Values in
between (50/150ms) were partial improvements but still audibly imperfect —
likely the playback device's own anti-pop fade-in ramp landing on top of
real audio rather than silence.

**Fix:** Shipped with pad_ms=250 — a middle ground that avoids both the
500ms no-op and the 0-150ms clipping range, without fully eliminating the
perceptual issue. Documented as a known minor limitation rather than
claimed fully fixed.

**Why it matters:** Not every audio artifact is worth chasing to zero,
especially on CPU-only TTS with a small model. Two things worth
remembering for a future project: measuring the waveform directly (not
trusting ear alone) is what caught the 50ms overcorrection before it
shipped as "fixed," and "more padding" doesn't monotonically mean
"safer" — check the boundary math before reaching for this same
trim-by-threshold pattern again.

## Phase 5 — BriefingRequest.city accepted but not wired through

**Note, not a bug:** BriefingRequest.city validates and is accepted by
POST /briefing/generate, but generate_briefing() doesn't actually use it --
get_weather() always reads config.CITY regardless of what's passed. Left
as-is deliberately for this phase; wiring it through is a small,
well-understood follow-up whenever there's a reason to actually override
city per-request.

## Phase 6 — pytest can't find project modules; pytest.ini needs -Encoding ascii

**Problem 1:** `pytest -v` failed with `ModuleNotFoundError: No module
named 'graph'` even though graph.py exists at the project root.

**Diagnosis:** pytest adds each test file's own directory to sys.path by
default, not the project root -- tests/test_graph.py had no way to find
graph.py one level up.

**Fix:** Added pytest.ini at the repo root with `pythonpath = .`

**Problem 2:** pytest then failed to parse that exact file:
`unexpected line: '\ufeff[pytest]'`

**Diagnosis:** Same root cause flagged back in Phase 1 -- PowerShell's
`Out-File -Encoding utf8` always writes a UTF-8 byte-order-mark.
pip-compile tolerated it; pytest's INI parser doesn't.

**Fix:** `Out-File -Encoding ascii` instead, since pytest.ini's content is
plain ASCII anyway.

**Why it matters:** This BOM issue has now bitten three times across this
project (requirements.in in Phase 1, and now this). Worth defaulting to
-Encoding ascii for any plain-text config file going forward, and only
reaching for utf8 when non-ASCII content actually requires it.

## Phase 7 — Containerized pipeline correctness vs. performance on constrained hardware

**Problem:** POST /briefing/generate through the containerized setup
(docker-compose.local.yml) took 15-30+ minutes per request, including on a
back-to-back call where the model should still have been warm.

**Diagnosis:** Same code, same model, same machine ran in seconds during
Phases 0-5 without Docker involved. The only changed variable is WSL2's
virtualization layer — the herald container (torch/kokoro/spacy resident)
competes for WSL2 VM memory while the host's Ollama process competes for
host memory, on an 8GB machine with little headroom for either. Not fully
confirmed via a live Task Manager read during a slow request, but the
before/after comparison is strong circumstantial evidence.

**Fix:** None needed at the application level — this is a resource
ceiling, not a code defect. Documented rather than chased further.
Correctness is proven; performance is not representative of what this
would look like on adequate hardware.

**Why it matters:** Correctness and performance are separate claims. This
container is proven correct on this hardware and would very likely run
dramatically faster on a machine with adequate RAM — worth remembering
before assuming a slow container run means broken code.

## Phase 8 — Disk-space crisis corrupted the host Ollama install

**Problem:** ollama.chat() failed with "llama-server binary not found",
searching eight plausible paths and finding none, despite ollama list and
ollama --version both working normally.

**Diagnosis:** Compute-backend DLLs (CUDA/ROCm/Vulkan) were all present and
correctly dated, but llama-server.exe itself was missing entirely. File
timestamps lined up with the exact window during Phase 7's Docker disk-space
crisis, when C: dropped to ~6GB free -- strongly suggesting Ollama's
background auto-updater ran during that window and silently failed
partway through extracting a new version.

**Fix:** Reinstalled Ollama over the existing install (irm
https://ollama.com/install.ps1 | iex). Repaired the missing binary without
touching already-pulled models, which live in a separate directory.

**Why it matters:** A disk-space crisis in one tool (Docker/WSL2) can
silently corrupt a completely unrelated program (Ollama) if it happens to
be mid-update at the same moment. Worth checking core dependencies with a
basic smoke test after any low-disk-space incident, not just the tool that
caused it.

## Phase 8 — Two real issues while testing the city/timezone feature

**Problem 1:** First requests after code changes kept returning old
(Hyderabad) data despite editing weather.py/clock.py/graph.py/main.py.

**Diagnosis:** docker compose up only rebuilds an image if one doesn't
already exist. Since herald-herald:latest was already built earlier,
every up/down/up cycle reused the stale image -- the container was
faithfully running pre-change code the whole time. The temperature
mismatch (32C "London" vs. real London weather) was the tell.

**Fix:** docker compose up --build forces a real rebuild. Going forward:
after any code change intended to run in Docker, use --build explicitly
rather than assume compose picked it up.

**Problem 2:** During the rebuild's first request, Kokoro's voice-file
HEAD-check to Hugging Face failed with DNS resolution errors, retried
5 times with backoff, then succeeded anyway once network came back.

**Diagnosis:** Transient network hiccup, likely related to the container
network settling right after a fresh build/network recreation. Not a
code bug -- huggingface_hub's own retry logic handled it correctly and
the request ultimately succeeded (84 words, valid response).

**Why it matters:** The --build habit is the one worth internalizing --
this bug pattern (editing code, testing in Docker, seeing no change take
effect) is easy to mistake for a code problem when it's actually a stale
image.