# main.py - MCP server for Databricks Genie (HTTP for Databricks Apps)
# Use cases when you cannot touch UC tables/sandbox from this app:
# - Tools: utilities Genie can call (time, SQL checks, docs, external APIs).
# - This app can still call Databricks APIs (jobs, workspace) if you add credentials.
from datetime import datetime, timezone
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-ad")

# ---------------------------------------------------------------------------
# Use-case summary (exposed as a tool so Genie can read it)
# ---------------------------------------------------------------------------

MCP_USE_CASES = """
mcp-ad use cases (no direct UC table/sandbox access from this app):

1) Utilities for Genie
   - get_current_time_utc: current time for scheduling or logging.
   - hello: simple test tool.

2) SQL helpers (no DB connection)
   - validate_sql_basic: basic sanity checks (parentheses, dangerous keywords).
   - format_sql_hint: suggest indentation/style for a SQL string.

3) Documentation / onboarding
   - list_mcp_capabilities: returns this use-case list and available tools.

4) Future (add credentials / app resources in Databricks):
   - Run Databricks jobs via REST API (e.g. run a job that queries tables).
   - List workspace or notebooks via Databricks API.
   - Call external APIs (Slack, CRM, internal services) and expose as tools.
   - Expose runbooks or FAQs as a resource so Genie can read them.
"""


@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone. Use for testing that the MCP is reachable."""
    return f"Hello, {name}!"


@mcp.tool()
def get_current_time_utc() -> str:
    """Return the current time in UTC (ISO format). Use for scheduling, logs, or time-sensitive answers."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@mcp.tool()
def list_mcp_capabilities() -> str:
    """List what this MCP server can do and suggested use cases. Call this when the user asks what the MCP does or what use cases it supports."""
    return MCP_USE_CASES.strip()


@mcp.tool()
def validate_sql_basic(sql: str) -> str:
    """Run basic sanity checks on a SQL string (no execution). Checks: balanced parentheses, and warns if dangerous keywords like DROP/DELETE/TRUNCATE appear. Returns a short report."""
    if not sql or not sql.strip():
        return "Error: SQL string is empty."
    report = []
    # Balanced parentheses
    open_count = sql.count("(") - sql.count(")")
    if open_count != 0:
        report.append(f"Parentheses: unbalanced (difference {open_count}).")
    else:
        report.append("Parentheses: balanced.")
    # Dangerous keywords (case-insensitive)
    upper = sql.upper()
    for keyword in ("DROP", "DELETE", "TRUNCATE", "ALTER"):
        if keyword in upper:
            report.append(f"Warning: '{keyword}' found. Ensure this is intended.")
    if len(report) == 1 and "balanced" in report[0]:
        report.append("No dangerous keywords detected.")
    return "\n".join(report)


@mcp.tool()
def format_sql_hint(sql: str) -> str:
    """Suggest simple formatting for a SQL string: normalize whitespace and suggest indentation for SELECT/FROM/WHERE. Does not execute SQL."""
    if not sql or not sql.strip():
        return "SQL is empty."
    # Normalize whitespace
    text = " ".join(sql.split())
    # Simple indentation hints
    hints = []
    for keyword in ("SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "LIMIT"):
        if keyword.upper() in text.upper():
            hints.append(f"  - Put each {keyword} clause on its own line for readability.")
    if not hints:
        return f"Normalized (single-line): {text[:200]}{'...' if len(text) > 200 else ''}"
    return "Suggestions:\n" + "\n".join(hints) + "\n\nNormalized (single-line): " + text[:200] + ("..." if len(text) > 200 else "")


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )