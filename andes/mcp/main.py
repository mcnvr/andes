#!/usr/bin/env python3
"""
    python -m mcp.main              # Run with STDIO (for Claude Desktop)
    python -m mcp.main --http       # Run with HTTP transport
    python -m mcp.main --http --port 8080  # Run on custom port

    NOTE: Some models may require https
"""

import argparse
import sys
from .server import mcp


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="ANDES MCP Server - Expose ANDES simulations to LLMs"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run with HTTP transport instead of STDIO"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )

    args = parser.parse_args()

    print(f"Starting ANDES MCP Server...", file=sys.stderr)

    if args.http:
        print(f"HTTP mode: {args.host}:{args.port}", file=sys.stderr)
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        print("STDIO mode (for Claude Desktop)", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
