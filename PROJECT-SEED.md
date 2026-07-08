# reolink-mcp — Project Seed

> Context brief for `/gsd-new-project`. Captures the decisions and research
> already made (2026-07-08) so project initialization doesn't re-derive them.
> Delete this file once `.planning/PROJECT.md` supersedes it.

## What

An open-source **MCP (Model Context Protocol) server for Reolink cameras**:
lets Claude / any MCP client see and control Reolink cameras on the local
network — snapshots, device state, AI detection events, PTZ presets, and
deterrence controls (spotlight, siren, IR).

**Market gap (verified 2026-07-08):** no dedicated Reolink MCP server exists on
GitHub, npm, or PyPI. Closest prior art: `dedsxc/mcp-frigate` (requires Frigate
NVR), `homeassistant-mcp` (requires Home Assistant). This is a first-mover
standalone niche.

## Locked decisions

1. **v1 scope: observe + safe controls.**
   - Observe: `list_cameras`, `get_capabilities`, `get_device_info`,
     `get_snapshot` (MCP image content block), `get_states`, `get_recent_events`
   - Safe controls: PTZ presets (`ptz_move_to_preset`, `list_presets`,
     `ptz_position`, `ptz_guard`), `set_siren`, `set_spotlight`,
     `set_ir_lights`, `set_white_led`
   - Deferred past v1: risky settings (privacy mask, recording config,
     encoding, network settings), full ~59-setter surface of reolink-aio.
   - Use MCP tool annotations (`readOnlyHint`, `destructiveHint`) so clients
     can gate approvals on observe vs. control.

2. **Architecture: direct-to-camera.** The server owns its own `reolink-aio`
   sessions, configured via its own YAML/env. Standalone product — no
   dependency on any other daemon/NVR. Document the Reolink concurrent-session
   limit caveat for users also running another system (e.g.,
   surveillance-security-ai) against the same cameras.

3. **Separate OSS project.** Own repo, own PyPI package, own license/CI.
   No code dependency on surveillance-security-ai in either direction — both
   independently use `reolink-aio`.

## Recommended stack (from prior research, confirm during new-project)

- Python >= 3.11 (floor forced by reolink-aio)
- Official `mcp` Python SDK (`FastMCP` server class); stdio transport first,
  streamable HTTP later. (`fastmcp` 2.x is the fallback if SDK ergonomics fall short.)
- `reolink-aio` 0.21.x — battle-tested (Home Assistant's pin), async, covers
  PTZ/presets/patrol/guard, siren, spotlight, IR/white LED, day-night,
  snapshots, AI-event push (ONVIF SWN + Baichuan TCP).
- pydantic + pydantic-settings (YAML config + env-var secrets — never
  passwords in YAML; follow `RMCP_CAMERAS__0__PASSWORD`-style nested overrides)
- uv + hatchling + ruff + pytest/pytest-asyncio; publish to PyPI so clients run
  it via `uvx reolink-mcp`; list in the MCP registry.

## v1 success shape

A user with a Reolink camera adds `reolink-mcp` to Claude Code/Desktop config,
asks "show me the front door camera", and gets a live snapshot; asks "turn on
the spotlight" and it happens (with client-side approval). Vertical first
slice: config + connect + `list_cameras` + `get_snapshot` against a real camera.

## Future direction (post-v1, roadmap candidates)

- Wider control surface (auto-tracking, two-way audio talk-down, quick replies,
  day/night & detection-sensitivity tuning)
- Event subscription tools / MCP resources for near-real-time AI detections
- Streamable HTTP transport + auth for remote clients
- Broader sensor ecosystem via same pattern (mmWave presence, contact,
  vibration — Zigbee/Matter) as sibling servers or extensions
