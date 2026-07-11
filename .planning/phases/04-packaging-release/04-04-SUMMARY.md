---
phase: 04-packaging-release
plan: 04
subsystem: release
tags: [pypi, testpypi, trusted-publishing, oidc, github-release, mcp-registry, uvx]

# Dependency graph
requires:
  - phase: 04-packaging-release
    provides: "04-01 ci.yml + packaging_smoke.py, 04-02 public README + config.example.yaml, 04-03 release metadata + CHANGELOG.md + server.json + release.yml"
provides:
  - "PyPI release reolink-mcp 1.0.0 (https://pypi.org/project/reolink-mcp/1.0.0/) installable via uvx reolink-mcp"
  - "GitHub Release v1.0.0 with CHANGELOG-derived notes"
  - "MCP Registry listing io.github.ed-dryha/reolink-mcp, version 1.0.0, status active"
  - "TestPyPI rehearsal 1.0.0 (D-04) completed before the real tag"
  - ".github/workflows/registry-publish.yml -- workflow_dispatch re-publish of server.json decoupled from the tag pipeline"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "OIDC publish jobs stay checkout-free: uv publish uses --publish-url (not a named pyproject index) because the publish job only downloads the dist artifact"
    - "MCP Registry re-publish is a workflow_dispatch workflow reading server.json from main -- never re-tag to fix registry metadata (tags drive the immutable PyPI path)"

key-files:
  created:
    - .github/workflows/registry-publish.yml
  modified:
    - .github/workflows/release.yml
    - server.json

key-decisions:
  - "release.yml rehearsal publish switched from `uv publish --index testpypi` to `--publish-url https://test.pypi.org/legacy/` -- the publish job has no checkout, so a named uv index (defined in pyproject.toml) is unresolvable there; publishing by URL also keeps repo content out of the OIDC job (supply-chain hygiene)"
  - "server.json description shortened 122 -> 99 chars: the MCP Registry enforces description <= 100 (422 on publish); pyproject.toml description deliberately left as-is (different display surface, no such limit)"
  - "Registry fix delivered via a new workflow_dispatch workflow rather than a new tag: any new tag re-drives the PyPI publish path, which is immutable/1.0.0-occupied"
  - "TestPyPI clean-env verify needed --index-strategy unsafe-best-match: a stale mcp==0.8.0.dev0 exists on TestPyPI and uv's anti-dependency-confusion default pins mcp to the first index carrying it (TestPyPI-only quirk, irrelevant to real PyPI)"

patterns-established:
  - "Rehearsal-first releases: every release tag is preceded by a -rcN tag that must publish and clean-env-install from TestPyPI before the real tag is pushed"

requirements-completed: [REL-01, REL-02]

# Metrics
duration: ~2h (including human web-UI setup and live CI/CD runs)
completed: 2026-07-11
---

# Phase 04 Plan 04: Execute the v1.0.0 Release Summary

The release is live end to end. Task 1 pushed local main (all Phase 1-4 work) to
github.com/ed-dryha/reolink-mcp (`ef971ca..ccefb71`, fast-forward). Task 2's four
human-only steps were completed and verified: PyPI + TestPyPI pending publishers
(reolink-mcp / ed-dryha / release.yml, environments pypi/testpypi), both GitHub
environments, and live CI proof via throwaway PR #1 (all 12 ci.yml jobs green,
merged). Task 3 ran the D-04 rehearsal and then the human-pushed real tag.

## Release timeline

1. `v1.0.0-rc1` — FAILED in publish-pypi: `uv publish --index testpypi` cannot
   resolve a named index in a checkout-free job ("No indexes were found").
   Fixed in `2dfd3ec` by publishing by URL. Nothing was uploaded, so the
   TestPyPI 1.0.0 slot stayed free.
2. `v1.0.0-rc2` — green: build → smoke → TestPyPI publish; github-release and
   publish-registry correctly skipped on the rehearsal branch. Verified:
   test.pypi.org/project/reolink-mcp/1.0.0/ live (wheel + sdist); clean-env
   `uvx --index test.pypi.org/simple ... reolink-mcp` installed 44 packages and
   exited non-zero with the curated `config error:` message.
3. `v1.0.0` — pushed by the human (the one irreversible step, by design).
   build, publish-pypi (pypi environment), github-release all green;
   publish-registry FAILED 422: description length 122 > registry limit 100.
4. Registry fix (`480a251`): server.json description shortened to 99 chars +
   new `registry-publish.yml` (workflow_dispatch). Human triggered it; green.

## Final verified state (REL-01/REL-02 acceptance)

- ✓ pypi.org/project/reolink-mcp/1.0.0/ exists; clean-env `uvx reolink-mcp`
  installs from real PyPI and fails loudly with the curated config error
- ✓ GitHub Release v1.0.0 exists with CHANGELOG-derived notes
- ✓ MCP Registry lists io.github.ed-dryha/reolink-mcp @ 1.0.0, status active
- ✓ TestPyPI rehearsal preceded the real tag (D-04)
- ✓ origin/main carries every commit from Plans 04-01 through 04-04

## Deviations

- Rule-1 fix: release.yml rehearsal publish `--index testpypi` → `--publish-url`
  (commit `2dfd3ec`), root cause: publish job is checkout-free by design.
- Rule-1 fix: server.json description 122 → 99 chars + registry-publish.yml
  workflow added (commit `480a251`), root cause: undocumented-in-plan registry
  422 limit of 100 chars on body.description.
- Stale tag `v1.0.0-rc1` still exists on origin pointing at the pre-fix commit;
  harmless (run failed, nothing published) — may be deleted for tidiness.

## Self-Check: PASSED

- All three tasks complete (Task 1 auto, Tasks 2-3 human gates confirmed)
- All 8 verification steps of Task 3 confirmed against live external services
- No STATE.md/ROADMAP.md modifications by this plan (orchestrator-owned)
