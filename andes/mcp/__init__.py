"""
ANDES MCP Server

Model Context Protocol server for ANDES power system simulation.
Exposes ANDES capabilities to LLMs through standardized MCP tools, resources, and prompts.
"""

__version__ = "0.1.0"

from .server import mcp

__all__ = ["mcp"]
