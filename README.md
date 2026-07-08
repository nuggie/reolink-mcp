# reolink-mcp

MCP (Model Context Protocol) server for Reolink cameras — see and control your
cameras from Claude or any MCP client: snapshots, device state, AI detection
events, PTZ presets, spotlight/siren/IR deterrence. Local network only, no cloud.

> **Status: pre-alpha.** Project is being bootstrapped — nothing usable yet.
> See `PROJECT-SEED.md` for scope and design decisions.

## Planned v1

- **Observe:** list cameras, capabilities, device info, snapshots, states, recent AI events
- **Safe controls:** PTZ presets, spotlight, siren, IR/white LED
- **Transport:** stdio (`uvx reolink-mcp`), config via YAML + env-var secrets

Built on [`reolink-aio`](https://github.com/starkillerOG/reolink_aio) and the
official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## License

MIT
