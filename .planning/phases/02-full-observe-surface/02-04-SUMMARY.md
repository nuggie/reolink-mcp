---
phase: 02-full-observe-surface
plan: 04
subsystem: testing
tags: [qa-harness, observe-tools, reolink-aio, pytest, mcp]

# Dependency graph
requires:
  - phase: 02-full-observe-surface
    provides: get_capabilities/get_states/get_recent_events (Plans 02-01/02-02) and the qa_phase2.py structural QA harness (Plan 02-03) this plan repairs
provides:
  - "scripts/qa_phase2.py's check_states validator (STATE_FIELD_VALIDATORS) matching get_states' real per-field return contract — fixes CR-01"
  - "RAW_TO_FRIENDLY_AI_TYPES module constant in observe.py, shared by get_capabilities and get_recent_events (WR-02)"
  - "get_states(full=True)'s status_led capability-gated instead of fabricated False (WR-03)"
  - "tests/test_qa_phase2_validators.py — hardware-free regression proof of the CR-01 fix"
affects: [phase-2-verification, human-uat-test-3]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-field validator dict (STATE_FIELD_VALIDATORS) replacing a blanket type-union check, for QA harnesses validating heterogeneous tri-state fields"
    - "Module-level shared vocabulary-conversion constant (RAW_TO_FRIENDLY_AI_TYPES) consumed by multiple tool functions instead of duplicated inline dict literals"

key-files:
  created:
    - tests/test_qa_phase2_validators.py
  modified:
    - scripts/qa_phase2.py
    - src/reolink_mcp/tools/observe.py
    - tests/tools/test_observe.py

key-decisions:
  - "CR-01 fix implements 02-REVIEW.md's exact suggested STATE_FIELD_VALIDATORS replacement rather than a novel design — the fix was already fully specified"
  - "get_capabilities' ai_detection_types now matches get_recent_events' friendly-name vocabulary (person/pet), with raw wire keys still available under full=True as raw_ai_types, mirroring get_recent_events' own full=True shape exactly"
  - "status_led gates on the raw host.supported(ch, 'status_led') string directly (not capabilities.gate()) since it is a full=True-only diagnostic field with no CAPABILITY_MAP entry — same precedent as the adjacent audio_alarm_enabled field"

requirements-completed: [HDWR-01]

# Metrics
duration: ~25min
completed: 2026-07-09
---

# Phase 2 Plan 4: QA Harness CR-01 Fix + observe.py Vocabulary/Gating Consistency Summary

**Fixed the qa_phase2.py check_states validator that guaranteed FAIL on every camera with day/night or siren support (CR-01), plus made get_capabilities' AI-type vocabulary and get_states(full=True)'s status_led gating consistent with the rest of the observe surface.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-07-09T20:18:00+03:00 (approx.)
- **Completed:** 2026-07-09T20:24:06+03:00
- **Tasks:** 2 of 3 completed (Task 3 is an operator checkpoint against real hardware — see below)
- **Files modified:** 3 modified, 1 created

## Accomplishments

- Fixed CR-01: `scripts/qa_phase2.py`'s `check_states` validator now matches `get_states`' actual per-field return contract (`day_night`: non-empty string or `"unsupported"`; `white_led`: dict or `"unsupported"`; `ir_lights`: bool or `"unsupported"`; `siren`: literal `"supported"`/`"unsupported"`) instead of a blanket bool/dict/`"unsupported"` check that rejected the server's own correct output
- Added `tests/test_qa_phase2_validators.py` — a hardware-free regression test that imports `scripts/qa_phase2.py` directly and proves the fix, including the exact 02-VERIFICATION.md repro payload producing zero problems
- Fixed WR-02: `get_capabilities`' `ai_detection_types` now returns friendly names (`"person"`/`"pet"`) matching `get_recent_events`'s vocabulary instead of leaking raw wire keys (`"people"`/`"dog_cat"`); raw values still available under `full=True` as `raw_ai_types`
- Fixed WR-03: `get_states(full=True)`'s `status_led` now reports `"unsupported"` when the camera has no status LED, instead of a fabricated `False`, bringing it into compliance with the tool's own D-09 discipline
- De-duplicated the raw-to-friendly AI-type conversion into a single module constant `RAW_TO_FRIENDLY_AI_TYPES`, consumed by both `get_capabilities` and `get_recent_events` (previously an inline dict literal duplicated only in `get_recent_events`)

## Task Commits

Each task was committed atomically, following RED/GREEN TDD discipline:

1. **Task 1: Fix CR-01 — qa_phase2.py check_states validator**
   - `c90af56` (test) — add failing regression test for CR-01 qa_phase2 state validators (RED — confirmed `ImportError: cannot import name 'STATE_FIELD_VALIDATORS'` against pre-fix code)
   - `c997fed` (fix) — CR-01: qa_phase2 check_states validator matches get_states' real contract (GREEN)
2. **Task 2: Fix WR-02 (friendly AI-type vocabulary) and WR-03 (status_led gating)**
   - `e7ae03a` (test) — add failing tests for WR-02/WR-03 (RED — confirmed 3 of 4 new/updated assertions failed against pre-fix `observe.py`; the 4th, `test_get_states_full_true_status_led_reports_state_when_supported`, verifies preserved passthrough behavior and was expected to pass in both states per the plan's own `<behavior>` spec)
   - `a0ffa5c` (feat) — WR-02/WR-03: friendly AI-type vocabulary and status_led capability gating (GREEN)

**Plan metadata:** SUMMARY.md commit (this plan, worktree mode — orchestrator merges and updates STATE.md/ROADMAP.md centrally)

_Note: Both tasks used `tdd="true"` — each has a `test(...)` RED commit followed by a `feat(...)`/`fix(...)` GREEN commit._

## Files Created/Modified

- `scripts/qa_phase2.py` - `STATE_FIELD_VALIDATORS` dict of per-field validator callables replaces `STATE_TRISTATE_FIELDS`'s blanket check; docstring updated to state the real per-field contract
- `tests/test_qa_phase2_validators.py` - New hardware-free test file: one test per validator's accept/reject behavior, plus the CR-01 regression repro-payload test
- `src/reolink_mcp/tools/observe.py` - `RAW_TO_FRIENDLY_AI_TYPES` module constant added; `get_capabilities` applies it to `ai_detection_types` and adds `raw_ai_types` under `full=True`; `get_recent_events`'s inline dict literal replaced with the shared constant (pure de-dup); `get_states(full=True)`'s `status_led` now capability-gated via `host.supported(ch, "status_led")`
- `tests/tools/test_observe.py` - Updated `test_get_capabilities_maps_curated_keys_and_ai_types`'s assertion to friendly names; added `test_get_capabilities_full_true_includes_raw_ai_types`, `test_get_states_full_true_status_led_unsupported_when_capability_absent`, `test_get_states_full_true_status_led_reports_state_when_supported`

## Decisions Made

- Implemented 02-REVIEW.md's exact suggested `STATE_FIELD_VALIDATORS` replacement for CR-01 rather than designing a new validator scheme — the fix was already fully specified by the code reviewer and independently re-confirmed by 02-VERIFICATION.md's hardware-free repro
- Kept `status_led`'s gating on the raw `host.supported(ch, "status_led")` string (not `capabilities.gate()`) since it has no `CAPABILITY_MAP` entry and is a `full=True`-only diagnostic field — matches the existing `audio_alarm_enabled` field's own gating style exactly, per the plan's interfaces section
- `get_recent_events`'s conversion-loop change is a pure de-duplication (swapping an inline dict literal for the new shared module constant) with no behavior change, verified by the full existing test suite passing unchanged

## Deviations from Plan

None - plan executed exactly as written for Tasks 1 and 2. Task 3 is a `checkpoint:human-verify` gated on real P437/P320 hardware access, which this worktree executor cannot perform — see "Next Phase Readiness" below.

## Issues Encountered

- Ruff flagged the initial single-line `RAW_TO_FRIENDLY_AI_TYPES = {...}` definition as `E501 line too long`. Reformatted to a multi-line dict literal; re-ran `ruff check` and the full test suite to confirm no other regressions. This was a cosmetic formatting fix within the same task, not tracked as a separate deviation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Tasks 1 and 2 are complete, committed, and fully verified:
- `uv run pytest tests/test_qa_phase2_validators.py -q` — 9 passed
- `uv run pytest tests/tools/test_observe.py -q` — 50 passed
- `uv run pytest tests/ -q` — 91 passed, zero regressions
- `uv run ruff check src/ tests/ scripts/` — clean

**Task 3 (checkpoint, blocking) is NOT complete** — it requires the operator to run `uv run python scripts/qa_phase2.py` against real P437/P320 hardware from a machine with LAN access to the cameras (outside this worktree's reach) and confirm:
1. `check_states` now prints PASS for both cameras (previously guaranteed FAIL regardless of server correctness — this is what CR-01 fixed)
2. `check_device_info`, `check_capabilities`, `check_recent_events` remain PASS (no regression from Task 2's `observe.py` changes)
3. `check_capabilities`' printed table shows `ai_detection_types` as friendly names (`person`/`vehicle`/`pet`), never raw wire keys

This is the same discipline as 02-03-PLAN.md Task 2 — no automated command exists for this task by design; real hardware is outside CI/mock/worktree reach. Once the operator confirms, the CR-01 gap from 02-VERIFICATION.md and Human-UAT test #3 are both closed and HDWR-01 can be marked complete.

---
*Phase: 02-full-observe-surface*
*Completed: 2026-07-09 (Tasks 1-2; Task 3 checkpoint pending operator hardware verification)*

## Self-Check: PASSED

All created/modified files verified present on disk; all 5 commit hashes (`c90af56`, `c997fed`, `e7ae03a`, `a0ffa5c`, `8e42443`) verified present in `git log --oneline --all`.
