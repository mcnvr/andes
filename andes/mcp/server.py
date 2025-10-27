from fastmcp import FastMCP
from .config import MCPConfig

mcp = FastMCP(MCPConfig.NAME)

from .tools.simulation import register_simulation_tools
from .tools.analysis import register_analysis_tools
from .tools.results import register_results_tools
from .resources import register_documentation_resources

register_simulation_tools(mcp)
register_analysis_tools(mcp)
register_results_tools(mcp)
register_documentation_resources(mcp)


@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about the ANDES MCP server"""
    return f"""
# ANDES MCP Server

Version: {MCPConfig.VERSION}
Description: {MCPConfig.DESCRIPTION}

## Available Tools

### Simulation Management
- list_available_cases: List all built-in ANDES test cases
- load_case: Load a case file and create a simulation session
- get_system_info: Get information about a loaded system
- list_sessions: List all active simulation sessions
- close_session: Close a simulation session

### Analysis Routines
- run_power_flow: Run power flow calculation
- run_time_domain: Run time-domain simulation
- run_eigenvalue: Run eigenvalue analysis

### Results Retrieval
- get_pflow_results: Get power flow results
- get_tds_results: Get time-domain simulation results
- list_tds_variables: List available TDS variables

## Available Resources

- andes://docs/llms.txt: Comprehensive ANDES documentation index in llms.txt format (read this to discover documentation URLs)
- server://info: This server information page

## Typical Workflow

1. list_available_cases() - Find a test case
2. load_case(case_path) - Load case and get session_id
3. run_power_flow(session_id) - Run power flow
4. run_time_domain(session_id) - Run transient simulation
5. get_tds_results(session_id) - Retrieve time series data

## Configuration

- Max sessions: {MCPConfig.MAX_SESSIONS}
- Session timeout: {MCPConfig.SESSION_TIMEOUT}s
- Cases directory: {MCPConfig.CASES_DIR}
"""


if __name__ == "__main__":
    mcp.run()
