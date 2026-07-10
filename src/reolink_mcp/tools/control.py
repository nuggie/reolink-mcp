"""Control tools (state-mutating): `set_siren` (Phase 3 Plan 1); `set_spotlight`,
`set_ir_lights`, `set_white_led` (Phase 3 Plan 1, Task 2).

Tool functions here are plain, undecorated `async def`s — registration with
`ToolAnnotations` happens explicitly in `tools/__init__.py`'s
`register_all(mcp, read_only)`, not via an `@mcp.tool` decorator in this
module. This module intentionally never imports `mcp` from `server.py`:
`server.py` constructs `mcp` and then imports `reolink_mcp.tools` to
register tools against it, so importing `mcp` here at module scope would be
circular (same convention as `tools/observe.py`).

Every tool is capability-gated via `capabilities.gate()`/`refusal_message()`
before any host mutation call (CTRL-10) and returns a read-back confirmation
dict — the resulting state, read from the camera after the command, not
just an echo of what was requested (D-14). `set_siren` is the one documented
exception: no live siren-state getter exists in reolink-aio, so it echoes
the accepted command with an explicit note instead.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import Context

from reolink_mcp.capabilities import gate, refusal_message
from reolink_mcp.errors import CameraError, classify_control_error

# D-01/D-02: a default duration keeps "sound the siren" from producing an
# indefinite blast, and a hard cap refuses (never clamps) any request over
# it — both validated BEFORE any host call.
SIREN_DEFAULT_DURATION_S = 5
SIREN_MAX_DURATION_S = 60


async def set_siren(
    camera: str,
    ctx: Context,
    action: Literal["sound", "stop"] = "sound",
    duration: int | None = None,
) -> dict[str, Any]:
    """Sound or stop `camera`'s siren (D-01..D-04).

    `action="sound"` with no `duration` produces a short ~5s burst
    (`SIREN_DEFAULT_DURATION_S`); an explicit `duration` over
    `SIREN_MAX_DURATION_S` (60s) is refused with a clear error naming the
    cap, never silently clamped. `action="stop"` silences an active siren
    immediately. Calling `action="sound"` again while already sounding is
    allowed (no refusal) — the camera's own firmware restarts the auto-off
    timer, no server-side code needed for that behavior (D-04).

    `duration=None` is NEVER passed to `host.set_siren` when
    `action="sound"` — that triggers reolink-aio's own indefinite "manual"
    mode, which D-01 forbids. No live siren-state getter exists in
    reolink-aio, so the returned dict echoes the accepted command rather
    than an observed state (D-14's documented exception)."""
    manager = ctx.request_context.lifespan_context.manager
    handle = await manager.get(camera)
    if not gate(handle, "siren"):
        raise CameraError(refusal_message(camera, "siren"))
    host, ch = handle.host, handle.channel

    note = (
        "no live siren-state getter exists in reolink-aio; this reflects "
        "the accepted command, not an observed state"
    )

    if action == "stop":
        try:
            await host.set_siren(ch, enable=False)
        except Exception as exc:
            raise CameraError(
                classify_control_error(exc, camera, manager.configured_host(camera))
            ) from exc
        return {"camera": camera, "action": "stop", "duration": None, "note": note}

    resolved_duration = duration if duration is not None else SIREN_DEFAULT_DURATION_S
    if resolved_duration > SIREN_MAX_DURATION_S:
        raise CameraError(
            f"camera '{camera}' siren duration {resolved_duration}s exceeds the "
            f"{SIREN_MAX_DURATION_S}s safety cap — request a duration of "
            f"{SIREN_MAX_DURATION_S}s or less"
        )

    try:
        await host.set_siren(ch, enable=True, duration=resolved_duration)
    except Exception as exc:
        raise CameraError(
            classify_control_error(exc, camera, manager.configured_host(camera))
        ) from exc
    return {
        "camera": camera,
        "action": "sound",
        "duration": resolved_duration,
        "note": note,
    }
