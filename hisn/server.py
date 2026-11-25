"""MCP server (official SDK v2): mcp.server.MCPServer, not FastMCP."""
from mcp.server import MCPServer

from hisn import tools
from hisn.retrieval import search_runbooks as _search

server = MCPServer("hisn-triage")


@server.tool()
def lookup_asset(host: str) -> dict:
    """Look up a host in the client asset inventory: owner, criticality and environment."""
    return tools.lookup_asset(host)


@server.tool()
def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search the incident runbooks and return the best matches with id, title, snippet and score."""
    return _search(query, k)


@server.tool()
def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    """Count earlier alerts with the same rule on the same agent within a time window ending at 'around'."""
    return tools.related_alerts(rule_id, agent, around, window_minutes)


if __name__ == "__main__":
    server.run()
