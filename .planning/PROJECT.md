# reolink-mcp

## What This Is

An open-source MCP (Model Context Protocol) server for Reolink cameras: lets Claude — or any MCP client — see and control Reolink cameras on the local network. Snapshots, device state, AI detection states, PTZ presets, and deterrence controls (spotlight, siren, IR/white LED). Local network only, no cloud. For anyone running an MCP client (Claude Code, Claude Desktop, etc.) with Reolink cameras on their LAN — starting with the author's own setup.

**Market gap (verified 2026-07-08):** no dedicated Reolink MCP server exists on GitHub, npm, or PyPI. Closest prior art requires a middleman: `dedsxc/mcp-frigate` (needs Frigate NVR), `homeassistant-mcp` (needs Home Assistant). This is a first-mover standalone niche.

## Core Value

A user with a Reolink camera adds `reolink-mcp` to their MCP client config, asks "show me the front door camera," and gets a live snapshot — direct to camera, no NVR or home-automation daemon in between.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Observe tools:**
- [ ] `list_cameras` — enumerate configured cameras
- [ ] `get_capabilities` — what a camera supports (PTZ, spotlight, siren, …)
- [ ] `get_device_info` — model, firmware, hardware details
- [ ] `get_snapshot` — live still image returned as an MCP image content block
- [ ] `get_states` — current device state (day/night, LED, siren, detection flags)
- [ ] `get_recent_events` — current AI detection states via on-demand polling (person/vehicle/animal flags); no background listener in v1

**Safe control tools:**
- [ ] `ptz_move_to_preset` / `list_presets` / `ptz_position` / `ptz_guard`
- [ ] `set_siren`
- [ ] `set_spotlight`
- [ ] `set_ir_lights`
- [ ] `set_white_led`
- [ ] MCP tool annotations (`readOnlyHint`, `destructiveHint`) so clients can gate approvals on observe vs. control

**Configuration & transport:**
- [ ] YAML config + env-var secrets (pydantic-settings; `RMCP_CAMERAS__0__PASSWORD`-style nested overrides — never passwords in YAML)
- [ ] stdio transport, runnable via `uvx reolink-mcp`

**Release (final phases of v1 — local functionality comes first):**
- [ ] Published to PyPI, listed in the MCP registry
- [ ] CI (GitHub Actions) running ruff + pytest on PRs
- [ ] End-user docs: README quickstart, Claude Desktop/Code config examples, camera compatibility notes, concurrent-session caveat

### Out of Scope

- Risky settings (privacy mask, recording config, encoding, network settings) — deferred past v1; mistakes are user-visible and hard to reverse
- Full ~59-setter surface of reolink-aio — v1 is observe + safe controls only
- Event subscription tools / MCP resources (ONVIF SWN push, Baichuan TCP listener) — post-v1; v1 polls AI states on demand instead
- Streamable HTTP transport + auth for remote clients — post-v1; stdio first
- Wider control surface (auto-tracking, two-way audio talk-down, quick replies, day/night & detection-sensitivity tuning) — post-v1 roadmap candidates
- Broader sensor ecosystem (mmWave presence, contact, vibration via Zigbee/Matter) — future sibling servers/extensions, not this package
- Any dependency on Frigate, Home Assistant, or surveillance-security-ai — standalone is the differentiator

## Context

- Seeded from `PROJECT-SEED.md` (2026-07-08), which captured prior research and locked decisions; that file is superseded by this document.
- Development hardware: real Reolink cameras exist on the author's network but are **shared** with another system (surveillance-security-ai) that also holds `reolink-aio` sessions. Reolink cameras have a concurrent-session limit — dev workflow must tolerate this, and end-user docs must document the caveat.
- Sibling project surveillance-security-ai independently uses `reolink-aio`; no code dependency in either direction.
- CI cannot assume camera hardware — tests run against mocks/fixtures of `reolink-aio`.
- `reolink-aio` 0.21.x is battle-tested (Home Assistant's pin), async, and covers the entire v1 surface: PTZ/presets/patrol/guard, siren, spotlight, IR/white LED, day-night, snapshots, AI-event push.

## Constraints

- **Tech stack**: Python ≥ 3.11 — floor forced by `reolink-aio`
- **Dependencies**: official `mcp` Python SDK (`FastMCP` server class); `fastmcp` 2.x is the fallback if SDK ergonomics fall short
- **Dependencies**: `reolink-aio` 0.21.x for all camera communication
- **Tooling**: uv + hatchling + ruff + pytest/pytest-asyncio
- **Security**: secrets via env vars only, never in YAML config
- **Compatibility**: must coexist with other systems holding sessions on the same cameras (document Reolink concurrent-session limit)
- **Distribution**: PyPI package runnable via `uvx reolink-mcp`; MCP registry listing

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 scope: observe + safe controls only | Deterrence toggles are reversible; risky settings (privacy mask, recording/network config) are not — defer them | — Pending |
| Direct-to-camera architecture | Standalone product; the niche exists precisely because prior art requires Frigate/Home Assistant | — Pending |
| Separate OSS project (own repo, PyPI package, license, CI) | No coupling to surveillance-security-ai in either direction | — Pending |
| `get_recent_events` polls current AI states in v1 | No background listener complexity in v1; push subscriptions (ONVIF/Baichuan) deferred to post-v1 | — Pending |
| MCP tool annotations (`readOnlyHint`/`destructiveHint`) | Lets clients gate approvals on observe vs. control without server-side policy | — Pending |
| Official `mcp` SDK (FastMCP) over `fastmcp` 2.x | Prefer official SDK; fallback documented if ergonomics fall short | — Pending |
| v1 milestone ends at published release, ordered local-first | Get everything working locally in early phases; packaging/publish/docs are the closing phases of the same milestone | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-08 after initialization*
