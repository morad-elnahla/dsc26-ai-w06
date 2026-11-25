# AI Usage

## How I used AI assistance

- Claude was used as a learning and guidance assistant. I asked it to explain the task requirements, clarify the related concepts, and help me understand the implementation approach step by step.
- I used that guidance to understand the work and make the implementation decisions. Claude was not used to generate the project files or write the implementation code.

## MCP SDK version

- I did not use the MCP v1 `FastMCP` API. I checked `hisn/server.py` and used `from mcp.server import MCPServer` with `@server.tool()`, as required by the task's MCP 2.2.0 SDK.

## One additional hostile model behavior

- The model may try to add an unexpected field to its final JSON response, such as `system_override`, to smuggle extra instructions into the triage note. The `TriageNote` schema forbids extra fields, so validation rejects that response. The loop asks the model to return valid JSON; after three invalid final responses, it stops and returns `needs_human` with reason `invalid_output`.
