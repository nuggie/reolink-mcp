---
phase: 01-core-snapshot-slice
verified: 2026-07-12T00:00:00Z
status: passed
score: 14/14 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 13/14
  gaps_closed:
    - "A correctly configured camera's password is available to the server but never appears in logs or errors (CONN-02) — validate_yaml_shape()'s ValidationError fallback (CR-01, the sibling of the 01-05 load_settings() fix) is now redacted: message built from e.errors() loc/type only; secret-like extra keys (password/Password/passwd/secret/token/credential, case-insensitive via _SECRET_KEY_RE against the key name in loc) get the curated CONN-02 message; 5 regression tests added (4 parametrized secret-like keys + 1 non-secret extra key), all passing (186/186 suite green). Closed at v1.0 milestone close, 2026-07-12."
  gaps_remaining: []
  regressions: []
closed_gaps_history:
  - truth: "A correctly configured camera's password is available to the server but never appears in logs or errors (CONN-02)"
    status: closed (2026-07-12 — validate_yaml_shape() redacted + regression tests; see re_verification.gaps_closed)
    reason: "NEW Critical finding (01-REVIEW.md CR-01, re-review dated 2026-07-09T09:04:50Z), independently reproduced by this verification via direct execution: 01-05's gap-closure fix redacted only load_settings()'s ValidationError fallback (config.py:179-215). It missed the structurally identical, unfixed sibling in validate_yaml_shape() (config.py:156): `raise SystemExit(f\"config error: camera '{name}' — {e}\") from e`. Pydantic v2's str(ValidationError) embeds `input_value=...` for every rejected extra field. The guard one line above (`if \"password\" in str(e):`, config.py:150) is a case-sensitive substring test against the *entire* ValidationError text, so it only catches a lowercase `password:` key. Any other rejected key in a CameraYamlEntry (extra='forbid') — a capitalized `Password:` (a very plausible authoring mistake), `passwd:`, `secret:`, `token:`, or any other typo'd/extra field — falls through to the raw-interpolation fallback and echoes the field's plaintext value verbatim into the SystemExit message, which is written to stderr and captured by MCP client logs (Claude Desktop/Code). This directly violates the project's core security constraint ('secrets via env vars only, never in YAML'), CONN-02's 'passwords are never read from YAML' guarantee, and ROADMAP.md Phase 1 Success Criterion 1's 'fails loudly at startup with a clear message' (a message that leaks the secret is not a safe failure). Reproduced live in this verification pass with four different key names (Password, passwd, secret, token) against the actual installed load_settings() — all four leaked the literal secret value 'SUPER-SECRET-HUNTER2' into str(SystemExit)."
    artifacts:
      - path: "src/reolink_mcp/config.py"
        issue: "Line 156: `raise SystemExit(f\"config error: camera '{name}' — {e}\") from e` inside validate_yaml_shape() interpolates the raw ValidationError, which embeds plaintext extra-field values via pydantic's input_value repr, for any rejected key that isn't a lowercase 'password' string match."
    missing:
      - "Redact validate_yaml_shape()'s ValidationError fallback the same way load_settings() was fixed in 01-05: build the message from e.errors()'s loc/type only, never str(e) or the raw error object."
      - "Detect the password-like-key case from e.errors()'s loc (case-insensitively, e.g. `str(loc[0]).lower() == \"password\"`) instead of a case-sensitive substring match against the full error text — this also fixes the false-positive risk noted in 01-REVIEW.md where a host value containing the word 'password' would currently trigger the curated password message incorrectly."
      - "Add a regression test (mirroring test_phantom_camera_env_var_never_leaks_password) using a capitalized `Password:` key in YAML, asserting the secret value and the substring 'input_value' never appear in the raised SystemExit message."
deferred: []
---

# Phase 1: Core Snapshot Slice Verification Report

**Phase Goal:** As a Reolink camera owner using an MCP client (Claude Code/Desktop), I want to configure my cameras in YAML with env-var-only passwords and get a live downscaled snapshot from a real camera by name, so that I can see my cameras directly through Claude with no NVR or home-automation daemon in between — proven session-safe against shared hardware.

**Verified:** 2026-07-12 (gap closure at v1.0 milestone close)
**Status:** passed
**Re-verification:** Yes — the 2026-07-09 pass (after 01-05 closed prior gaps G1/G2) found one remaining Critical (CR-01: validate_yaml_shape() raw-ValidationError secret leak, config.py:156). Closed 2026-07-12 during v1.0 milestone close: fallback message now built from e.errors() loc/type only; secret-like extra keys detected case-insensitively from the key name in loc (fixes the false-positive risk of the old substring guard too); 5 regression tests added (Password/passwd/secret/token + non-secret extra key), full suite 186/186 green, ruff clean.

## User Flow Coverage (MVP mode)

**Mode:** mvp (per ROADMAP.md `**Mode:** mvp` under Phase 1)
User story: «As a Reolink camera owner using an MCP client (Claude Code/Desktop), I want to configure my cameras in YAML with env-var-only passwords and get a live downscaled snapshot from a real camera by name, so that I can see my cameras directly through Claude with no NVR or home-automation daemon in between — proven session-safe against shared hardware.»
Format validated: `gsd-sdk query user-story.validate` → `valid: true`.

| Step | Expected | Evidence | Status |
|------|----------|----------|--------|
| 1. Configure cameras in YAML + env-var passwords | Named-map YAML (`host`, `username`) + `RMCP_CAMERAS__<name>__PASSWORD`; a `password:` key in YAML or a missing env var fails loudly with a clear, named error that never leaks the secret | `src/reolink_mcp/config.py` `Settings`/`CameraYamlEntry`; `tests/test_config.py` 6/6 green. **However**, a case-variant or otherwise-mistyped secret-like key (e.g. `Password:` capitalized) does NOT fail safely — it leaks the plaintext value into the SystemExit text (reproduced live, see Gaps below). | ✗ PARTIAL — happy path + the two documented failure modes are clean; an adjacent, easily-triggered failure mode leaks the secret |
| 2. Add server to a real MCP client over stdio | `initialize` handshake completes without corrupting stdout; all logging to stderr | `tests/test_stdout_purity.py` (real subprocess + real SDK client, 2/2 pass); live-confirmed 14+ clean handshakes across 10 restarts per 01-04-SUMMARY.md | ✓ VERIFIED |
| 3. Ask for a camera by name, get a live downscaled snapshot | `get_snapshot(camera)` returns a native `Image` content block + caption, sub-then-main fallback, unconditionally downscaled ~1280px | `tools/observe.py::get_snapshot`; `tests/tools/test_observe.py` (16 tests, including the 4 new CR-02 regression tests) all pass; live-confirmed real 640x360/896x512 images from P437/P320 per 01-04-SUMMARY.md | ✓ VERIFIED |
| 4. Outcome: see cameras directly through Claude, session-safe against shared hardware | No NVR/daemon in the path (direct `Host` per camera); coexists with `surveillance-security-ai` across repeated restarts without session exhaustion | `manager.py` (sole `Host(` construction site); 01-04-SUMMARY.md Checkpoint Result — 10/10 clean restarts, zero session-limit errors, operator-confirmed `surveillance-security-ai` unaffected | ✓ VERIFIED |

Step 1 does not pass cleanly: the "fails loudly with a clear message" contract is broken for a specific, plausible input (see Observable Truths #3 and Gaps below). Per the decision tree (any truth FAILED → `gaps_found`), the overall phase status is `gaps_found` even though 3 of 4 flow steps are clean.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can define cameras (name, host, username) in YAML with `RMCP_CAMERAS__<name>__PASSWORD` env-var-only passwords (CONN-01) | ✓ VERIFIED | `config.py` `Settings`/`CameraYamlEntry`/`CameraConfig`; `tests/test_config.py::test_env_override_merges_into_named_map` passes. Live-confirmed per 01-04-SUMMARY.md (P437/P320 connected via real YAML+env config). No regression: unchanged by 01-05. |
| 2 | A `password:` key in YAML, or a missing password env var, fails startup with a clear, named `SystemExit` (CONN-02, roadmap SC1) | ✓ VERIFIED (for these two literal cases) | `validate_yaml_shape()` (config.py:139-156) rejects a lowercase `password:` key with a named message; `load_settings()`'s `ValidationError` handler (config.py:181-189) catches the missing-password case with a named message. `tests/test_config.py` — both cases green. |
| 3 | A correctly-configured camera's password never appears in logs or errors (CONN-02) | **✗ FAILED** | The 01-05 fix closed the previously-reported leak (`load_settings()`'s own fallback, config.py:209-215 — now redacted, confirmed via `test_phantom_camera_env_var_never_leaks_password`). **New leak found and reproduced live in this verification**: `validate_yaml_shape()`'s sibling fallback (config.py:156) still interpolates the raw `ValidationError`, leaking the plaintext value of any non-lowercase-`password` extra/typo'd YAML key (`Password`, `passwd`, `secret`, `token` all reproduced). See Gaps G1 below. |
| 4 | Server never constructs more than one `Host` per camera for the process lifetime (CONN-03) | ✓ VERIFIED | `manager.py`'s `CameraManager.get()` caches `CameraHandle` behind a per-name `asyncio.Lock`; `tests/test_manager.py` concurrency test passes. `grep -rn "Host(" src/` — `manager.py` is the sole construction site (re-confirmed this pass). No changes to `manager.py` since prior verification. |
| 5 | A camera is contacted only on first tool call, never at startup (D-06) | ✓ VERIFIED | `CameraManager.__init__` (manager.py:59-65) performs no I/O; `app_lifespan` calls `load_settings()` + `CameraManager(...)` only. `tests/test_manager.py::test_constructor_performs_zero_io` passes. Unchanged. |
| 6 | `logout()` is attempted for every *connected* camera on shutdown; one failure never blocks the others (CONN-03) | ✓ VERIFIED, with WARNING | `close_all()` (manager.py:114-121) uses `asyncio.gather(..., return_exceptions=True)`; `tests/test_manager.py::test_close_all_is_exception_tolerant` passes. **Unchanged caveat (WR-01, 01-REVIEW.md):** a failed connect attempt is never cached and thus never logged out, leaking an `aiohttp.ClientSession` per failed attempt — still unfixed, tracked as WARNING (not a blocker; not re-litigated by this pass, no regression). |
| 7 | An unknown camera name produces a self-correcting error listing configured camera names (CONN-04/05, D-04) | ✓ VERIFIED | `unknown_camera_message()` (`errors.py:94-97`); `tests/test_errors.py`, `tests/test_manager.py`, `tests/tools/test_observe.py` unknown-camera cases all pass. Unchanged. |
| 8 | Offline camera, wrong credentials, and session-limit conditions each produce a distinct, actionable error message — never generic/misleading, including for `get_snapshot`'s own stream-fetch failures (CONN-04, CONN-05, roadmap SC4) | ✓ VERIFIED (gap closed) | `classify_reolink_error()` (`errors.py`) fully implements the matcher table, proven at both the manager/`list_cameras` layer AND now `get_snapshot`'s own sub/main stream-fetch failures. `observe.py:128-161` retains `last_exc` per attempt and classifies it via `classify_reolink_error` when both attempts produce no data; `_is_auth_or_session_failure()` (observe.py:25-37) short-circuits the main retry after `CredentialsInvalidError`/session-limit `LoginError`. 4 new tests (`test_get_snapshot_sub_raises_reolink_error_falls_back_to_main`, `test_get_snapshot_both_streams_raise_reolink_error_classifies_last_exc`, `test_get_snapshot_sub_credentials_invalid_raises_without_retrying_main`, `test_get_snapshot_sub_session_limit_raises_without_retrying_main`) verified present and passing. Confirmed by direct code read, not just SUMMARY claim. |
| 9 | Server completes the MCP `initialize` handshake over real stdio without corrupting stdout (SAFE-03) | ✓ VERIFIED | `tests/test_stdout_purity.py` — real SDK `stdio_client` handshake + raw subprocess stdout-byte read, both pass. Unchanged. Live-confirmed 14+ clean handshakes (01-04-SUMMARY.md). |
| 10 | All log output goes to stderr only, never stdout (SAFE-03) | ✓ VERIFIED | `__main__.py:15-19` configures `logging.basicConfig(stream=sys.stderr, ...)` before any `reolink_mcp` import; `grep -c "print(" src/reolink_mcp/**/*.py` → 0; ruff `T201` passes. Unchanged. |
| 11 | User can call `list_cameras` and see every configured camera with connection status, model, host (OBSV-01, roadmap SC2) | ✓ VERIFIED | `tools/observe.py::list_cameras`; `tests/tools/test_observe.py::test_list_cameras_two_online_returns_full_rows` (real MCP protocol path) passes. Live-confirmed (01-04-SUMMARY.md). Unchanged. |
| 12 | One unreachable camera never prevents `list_cameras` from returning the healthy cameras (D-07) | ✓ VERIFIED | `_probe()`'s per-camera `try/except` in `observe.py:47-90`; `tests/tools/test_observe.py::test_list_cameras_partial_failure_reuses_curated_message` passes. Unchanged. |
| 13 | `get_snapshot` returns a native image content block + text caption (camera, timestamp, resolution), sub-stream first with main-stream fallback, unconditionally downscaled to ~1280px/quality 80 (OBSV-04, roadmap SC3) | ✓ VERIFIED | `tools/observe.py::get_snapshot`; downscale/no-upscale/caption tests pass. Live-confirmed real images from both cameras, ≤1280px long edge (01-04-SUMMARY.md). Unchanged mechanism (only the error-handling paths around it changed in 01-05). |
| 14 | Server coexists with `surveillance-security-ai` holding sessions on the same cameras across repeated restarts without session exhaustion (HDWR-03, roadmap SC5) | ✓ VERIFIED (live) | 01-04-SUMMARY.md Checkpoint Result: "10/10 consecutive restarts, zero session-limit errors, `surveillance-security-ai` unaffected (operator-confirmed)." Accepted as real-hardware evidence per this phase's established human checkpoint; not re-litigated. No code touched by 01-05 affects this path. |

**Score:** 13/14 truths verified (1 FAILED — a newly-discovered Critical, `01-REVIEW.md` CR-01, distinct from and not covered by the two prior gaps 01-05 closed)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/reolink_mcp/config.py` | Named-map Settings, two-stage validation, no secret leakage on any failure path | ✗ VERIFIED WITH DEFECT | Exists, substantive (215 lines), wired (imported by `manager.py`, `server.py`). `load_settings()`'s own fallback is now redacted (01-05 fix, confirmed). `validate_yaml_shape()`'s sibling fallback (line 156) is not — reproduced live leak, see gap G1. |
| `src/reolink_mcp/errors.py` | `classify_reolink_error`, `CameraError`, `UnknownCameraError` | ✓ VERIFIED | 97 lines, unchanged, wired into `manager.py` and `tools/observe.py`. `tests/test_errors.py` 8/8 green. |
| `src/reolink_mcp/manager.py` | `CameraHandle`, `CameraManager` | ✓ VERIFIED, with WARNING | 127 lines, unchanged since prior verification. `close_all()` exception-tolerant; WR-01 (failed-connect session leak) still open, non-blocking. |
| `src/reolink_mcp/server.py` | FastMCP instance, `app_lifespan`, `AppContext` | ✓ VERIFIED | 50 lines, unchanged, wired (`__main__.py` imports `mcp`). |
| `src/reolink_mcp/__main__.py` | stderr-first logging, stdio entrypoint | ✓ VERIFIED | 29 lines, unchanged; logging configured before any `reolink_mcp` import. |
| `src/reolink_mcp/tools/observe.py` | `list_cameras`, `get_snapshot` | ✓ VERIFIED (gap closed) | 178 lines (was 144). `get_snapshot` now retains `last_exc` and classifies it via `classify_reolink_error`; `_is_auth_or_session_failure()` added. Confirmed by direct read, not SUMMARY claim. |
| `tests/test_config.py` | Config regression coverage including phantom-camera leak guard | ✓ VERIFIED (partial coverage) | 6 test functions (was 5), all green. `test_phantom_camera_env_var_never_leaks_password` correctly covers the G1 scenario it targets. **Gap:** no test covers a capitalized/mistyped secret-like YAML key — the exact scenario where the new CR-01 leak lives (confirmed via `grep -n "Password" tests/test_config.py` → no matches). |
| `tests/tools/test_observe.py` | `get_snapshot` ReolinkError-raising stream-attempt coverage | ✓ VERIFIED | 16 test functions (was 12), all green, including all 4 new CR-02 regression tests. |
| `tests/test_stdout_purity.py` | Real-subprocess stdio integration test | ✓ VERIFIED | 129 lines, unchanged, both tests pass. |
| `scripts/qa_phase1.py` | Real-hardware QA harness | ✓ VERIFIED (exists, used) | Referenced by 01-04-SUMMARY.md as the tool used for the live P437/P320 checkpoint. Not independently re-run against real hardware by this verification pass (no LAN access); accepted per the operator-approved live checkpoint already recorded. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `config.py` | env vars `RMCP_CAMERAS__<name>__PASSWORD` | `env_nested_delimiter="__"` over named-map `Settings.cameras` | WIRED | `config.py:107`; proven by passing merge test. Unchanged. |
| `config.py::validate_yaml_shape` | pydantic `ValidationError` | redacted loc/type-only message, no raw `str(e)` interpolation | **NOT WIRED (regression from the load_settings() fix — the sibling function was never updated)** | `config.py:156` still does `f"config error: camera '{name}' — {e}"`, directly interpolating the raw exception. This is the gap-closure pattern 01-05 established for `load_settings()` (config.py:209-215) but did not apply here. |
| `manager.py` | `errors.py` | `classify_reolink_error(exc, name, host)` inside `CameraManager.get()` | WIRED | `manager.py:94-97`. Unchanged. |
| `manager.py` | `reolink_aio.api.Host` | `Host(host=..., username=..., password=..., timeout=10)`, `get_host_data()` | WIRED | `manager.py:86-93`; sole `Host(` construction site in `src/`. |
| `tools/observe.py` | `manager.py` | `ctx.request_context.lifespan_context.manager` | WIRED | `observe.py:45, 111`. |
| `server.py` | `config.py` | `load_settings()` inside `app_lifespan` | WIRED | Unchanged. |
| `tools/observe.py::get_snapshot` | Pillow | `Image.open(...).convert("RGB").thumbnail((1280,1280), LANCZOS)` | WIRED | `observe.py:167-168`; proven by downscale test. |
| `tools/observe.py::get_snapshot` | `errors.py::classify_reolink_error` | curated translation on stream-fetch failure, including raised `ReolinkError` (not just `None`-returning) attempts | **WIRED (gap closed)** | `observe.py:128-161` — `last_exc` retained per attempt, classified via `classify_reolink_error` when both attempts produce no data; `_is_auth_or_session_failure` short-circuits main retry on auth/session failure. Confirmed by direct code read and 4 passing regression tests, matching the exact scenarios the previous verification found broken. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `list_cameras` | `handle.host.model`, connection status | `manager.get(name)` → `Host.get_host_data()` (real reolink-aio HTTP call) | Yes — live-confirmed against P437/P320 | FLOWING |
| `get_snapshot` | `data` (JPEG bytes) | `handle.host.get_snapshot(channel, stream=...)` (real reolink-aio HTTP call) | Yes — live-confirmed | FLOWING |
| `load_settings` error path | `SystemExit` message text | `e.errors()` (redacted) in `load_settings()`; raw `str(e)` (unredacted) in `validate_yaml_shape()` | Partially — one call site now produces a redacted, secret-free message; the other still echoes raw field values | ⚠️ HOLLOW (one of two error-message code paths still connects raw secret data to a user-visible/logged message) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite executes cleanly | `uv run pytest tests/ -q` | 38 passed | PASS |
| Lint clean (incl. `T201` stdout-purity rule) | `uv run ruff check src/ tests/ scripts/` | "All checks passed!" | PASS |
| No debt markers in phase-modified files | `grep -rn "TBD\|FIXME\|XXX" src/reolink_mcp/ tests/ scripts/` | no matches | PASS |
| `validate_yaml_shape()` leaks plaintext secret for a capitalized `Password:` YAML key | Live `load_settings()` invocation against a temp YAML with `Password: SUPER-SECRET-HUNTER2` | `SystemExit` message contains `input_value='SUPER-SECRET-HUNTER2'` verbatim | **FAIL** |
| Same leak reproduced for other secret-like keys (`passwd`, `secret`, `token`) | Live `load_settings()` invocation, one run per key | All four leaked the literal secret value | **FAIL** |
| `load_settings()`'s own (01-05-fixed) fallback no longer leaks for the phantom-camera scenario | `uv run pytest tests/test_config.py::test_phantom_camera_env_var_never_leaks_password -v` | 1 passed | PASS |
| `get_snapshot` classifies its own raised `ReolinkError`s via `classify_reolink_error` (not just `None`-returning streams) | `uv run pytest tests/tools/test_observe.py -k "reolink_error or credentials_invalid or session_limit" -v` | 4 passed | PASS |
| Sole `Host(` construction site remains `manager.py` (no regression) | `grep -rn "Host(" src/reolink_mcp/*.py src/reolink_mcp/tools/*.py` | 1 match (`manager.py:86`) | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` files exist and none are referenced by any Phase 1 PLAN/SUMMARY. Step 7c: SKIPPED — not applicable (real-hardware validation was performed via the documented human checkpoint, see Requirements Coverage / HDWR-03).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| CONN-01 | 01-01 | Configure cameras in YAML (name, host, username) | SATISFIED | `config.py`, `tests/test_config.py`; live-confirmed. |
| CONN-02 | 01-01, 01-05 | Passwords via env vars only, never YAML; never appears in logs/errors | **BLOCKED — new CR-01** | The phantom-camera leak (01-05's target) is fixed. A structurally identical leak in `validate_yaml_shape()`'s own fallback remains, reproducible for any non-lowercase-`password` rejected YAML key. |
| CONN-03 | 01-02 | One long-lived session per camera, lazy login, guaranteed logout | SATISFIED, with WARNING | Unchanged from prior verification; WR-01 (failed-connect session leak) still open, non-blocking. |
| CONN-04 | 01-02, 01-05 | Distinct actionable error for session-limit (`rspCode: -5`) | SATISFIED (gap closed) | Correct at `classify_reolink_error`/`CameraManager.get()`/`list_cameras` layer AND now `get_snapshot`'s own stream-fetch path (01-05 fix confirmed by code read + 4 passing tests). |
| CONN-05 | 01-02, 01-05 | Actionable text for offline/wrong-credentials, never raw traceback | SATISFIED (gap closed) | Same closure as CONN-04. |
| OBSV-01 | 01-03 | `list_cameras` with connection status | SATISFIED | Unit + live-confirmed, unchanged. |
| OBSV-04 | 01-04 | `get_snapshot` as native image content block, unconditionally downscaled | SATISFIED | Image/caption/downscale mechanism fully proven (unit + live), unchanged. |
| SAFE-03 | 01-03 | stdout reserved for MCP protocol; all logging to stderr | SATISFIED | Real-subprocess test + live-confirmed, unchanged. (Note: the CR-01 leak goes to stderr, not stdout — it does not violate SAFE-03's literal stdout-purity contract, but it does violate CONN-02 and the project's core secrets constraint; tracked there.) |
| HDWR-03 | 01-04 | Coexistence with `surveillance-security-ai`, no session exhaustion across restarts | SATISFIED (live) | 01-04-SUMMARY.md Checkpoint Result, unchanged, not re-litigated. |

No orphaned requirements: all 9 requirement IDs declared across the phase's plans (`CONN-01..05, OBSV-01, OBSV-04, SAFE-03, HDWR-03`) match REQUIREMENTS.md's Phase 1 traceability rows exactly (verified via direct grep of `.planning/REQUIREMENTS.md`).

### Anti-Patterns Found

Sourced from `01-REVIEW.md` (re-review, 2026-07-09T09:04:50Z) and cross-checked directly against current source in this verification pass.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/reolink_mcp/config.py` | 156 | Raw `ValidationError` interpolated into user-facing `SystemExit` message inside `validate_yaml_shape()` | 🛑 BLOCKER (CR-01, new) | Plaintext secret-like YAML values (capitalized `Password`, `passwd`, `secret`, `token`, or any mistyped extra field) leak into stderr/MCP client logs. Independently reproduced live in this verification for 4 different key names. |
| `src/reolink_mcp/manager.py` | 86-97 | Failed `Host()` connect is never `logout()`-ed or otherwise closed before the `CameraError` is raised | ⚠️ WARNING (WR-01, carried over, unfixed) | Leaks an `aiohttp.ClientSession` on every failed connect attempt. |
| `src/reolink_mcp/config.py` | 62-78, 139-148 | Non-dict/non-str camera entries and malformed YAML raise raw `TypeError`/`yaml.YAMLError` instead of a named `SystemExit` | ⚠️ WARNING (WR-02, carried over, unfixed) | Docstring's "every failure mode raises a named SystemExit" claim is false for these inputs. |
| `src/reolink_mcp/server.py` / `__main__.py` | 33-45 / 24-25 | `SystemExit` inside the lifespan surfaces as a `BaseExceptionGroup` traceback wall | ⚠️ WARNING (WR-03, carried over, unfixed) | Curated message buried at the bottom of a ~50-line traceback; SAFE-03 (stdout purity) still holds, but the "loud, clear, actionable" startup-error UX is undermined. |
| `src/reolink_mcp/errors.py` | 66-68 | Session-limit matcher `"-5" in str(exc)` is unanchored | ⚠️ WARNING (WR-04, carried over, unfixed) | Possible false-positive session-limit classification. |
| `src/reolink_mcp/errors.py` / `__main__.py` | 84-90 / 15-19 | "see server logs" messages point at logs suppressed at the default INFO level | ⚠️ WARNING (WR-05, carried over, unfixed) | Operator guidance is misleading in a default run. |
| `src/reolink_mcp/config.py` | 43 | Camera-name regex permits leading/trailing/doubled underscores, unbindable by `env_nested_delimiter="__"` | ⚠️ WARNING (WR-06, carried over, unfixed) | Confusing "no password" error even when the env var was set exactly as instructed. |
| `src/reolink_mcp/config.py` | 108 | `.env` file loaded relative to `cwd`, uncontrolled by a stdio server | ℹ️ INFO (WR-07, carried over) | Already worked around twice in this phase's own test suite. |
| `src/reolink_mcp/tools/observe.py` | 167-170 | Corrupt/undecodable snapshot bytes crash `get_snapshot` with a raw PIL traceback | ⚠️ WARNING (WR-08, new) | Breaks the "curated CameraError for every failure mode" discipline for untrusted, camera-supplied image bytes. |
| `src/reolink_mcp/tools/observe.py` | 48-56 | 12s probe budget does not actually sit above `manager.get()`'s true worst-case duration (multiple sequential awaited calls, no internal timeout) | ⚠️ WARNING (WR-09, new) | The session-leak/cancellation scenario the budget increase was meant to avoid remains reachable for a slow-but-responding camera. |
| `src/reolink_mcp/tools/observe.py` | 25-37, `errors.py` 66-68 | `_is_auth_or_session_failure` duplicates (rather than shares) the session-limit matcher it promises never to diverge from | ℹ️ INFO (IN-02, new) | Copy-paste is exactly how the two will diverge if one is fixed (e.g. WR-04's anchor) without the other. |
| `src/reolink_mcp/manager.py` | 52, 99 | `CameraHandle.connected` is write-only (never read, never set `False`) | ℹ️ INFO (IN-03, new) | Misleading dead field. |
| `tests/tools/test_observe.py` | 184 | Timing assertion in the concurrency test is flaky-prone (`elapsed < delay * 2`) | ℹ️ INFO (IN-04, carried over) | Possible CI flake, not a functional defect. |
| `src/reolink_mcp/tools/observe.py` | 78-80 | Stale comment references removed `asyncio.timeout(3)` (actual value is 12) | ℹ️ INFO (IN-01, carried over) | Documentation drift only. |

No unresolved `TBD`/`FIXME`/`XXX` debt markers found in any file modified by this phase (re-confirmed this pass: `grep -rn "TBD\|FIXME\|XXX" src/reolink_mcp/ tests/ scripts/` — no matches).

### Human Verification Required

None outstanding. The phase's designed human checkpoint (`01-04-PLAN.md` Task 2) was already executed and operator-approved on 2026-07-09 against real P437/P320 hardware (see `01-04-SUMMARY.md` Checkpoint Result), and this verification does not re-request it. The one remaining gap (CR-01 in `validate_yaml_shape()`) is a code-level defect, independently reproducible without hardware — it does not require a new human checkpoint, only a closure plan (mirroring 01-05's own pattern, applied to the sibling function it missed).

### Gaps Summary

01-05's gap-closure plan correctly and verifiably fixed both BLOCKER gaps from the prior verification pass: `load_settings()`'s `ValidationError` fallback no longer leaks a phantom-camera's password (confirmed via a passing regression test and direct code read), and `get_snapshot` now classifies its own stream-fetch `ReolinkError`s through the curated `classify_reolink_error` taxonomy instead of collapsing them into a generic message (confirmed via 4 new passing regression tests and direct code read). The full test suite (38/38) passes, lint is clean, and no regressions were found in any of the 12 previously-verified truths.

However, an independent fresh code review (`01-REVIEW.md`, re-reviewed 2026-07-09T09:04:50Z, standard depth) found — and this verification independently reproduced by direct execution — a **new** Critical: `validate_yaml_shape()` (config.py:156) has the exact same class of defect that `load_settings()` was fixed for in 01-05, but in a sibling function the gap-closure plan's scope never touched. Any YAML camera entry with a rejected extra/mistyped key that isn't literally the lowercase string `password` (a capitalized `Password:` — a very ordinary authoring slip — or `passwd`/`secret`/`token`/any other typo) falls through to a fallback that interpolates the raw `ValidationError`, and pydantic v2 embeds the plaintext field value in that error's string form. This was reproduced live against the actual `load_settings()` entry point in this verification, with four different key names, each leaking the literal secret text.

This is squarely within Phase 1's stated scope: it violates CONN-02 ("passwords are never read from YAML" — implicitly, and never leaked when a related config mistake is made), the project's own core security constraint ("secrets via env vars only, never in YAML"), and ROADMAP.md's Phase 1 Success Criterion 1 ("a password in YAML or a missing env var fails loudly at startup with a clear message" — a message that echoes the secret plaintext is not a safe failure mode). It is a narrower, more easily-triggered variant of the exact vulnerability class 01-05 was built to close — the fix pattern already exists in the same file, one function away, and simply needs to be applied to `validate_yaml_shape()` as well.

Per the goal-backward decision tree, one FAILED truth is sufficient to keep the phase at `gaps_found` regardless of the other 13 truths passing cleanly. This is a small, well-scoped, already-precedented fix (the 01-05 plan is the template) — recommend a focused gap-closure plan (01-06) applying the same redaction discipline to `validate_yaml_shape()`'s fallback, plus a regression test using a capitalized `Password:` key, before Phase 1 is considered fully closed.

---

_Verified: 2026-07-09T09:09:59Z_
_Verifier: Claude (gsd-verifier)_
