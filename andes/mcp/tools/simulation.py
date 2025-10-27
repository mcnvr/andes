from typing import Optional
import andes
from ..config import MCPConfig
from ..utils import get_session_manager, serialize_system_info


def register_simulation_tools(mcp):
    """Register simulation tools with the MCP server"""

    @mcp.tool()
    def list_available_cases() -> dict:
        """
        List all available built-in ANDES test cases.

        Returns a dictionary containing:
        - cases: List of available case file paths
        - count: Total number of available cases

        Example:
        {
            "cases": ["ieee14/ieee14.xlsx", "kundur/kundur_full.xlsx", ...],
            "count": 75
        }
        """
        cases = MCPConfig.list_all_cases()
        return {
            "cases": cases,
            "count": len(cases),
            "cases_dir": str(MCPConfig.CASES_DIR),
        }

    @mcp.tool()
    def load_case(case_path: str, setup: bool = True, no_output: bool = True) -> dict:
        """
        Load an ANDES case file and create a new simulation session.

        Parameters:
        - case_path: Relative path to case file (e.g., "ieee14/ieee14.xlsx") or absolute path
        - setup: Whether to setup the system after loading (default: True)
        - no_output: Suppress file output generation (default: True)

        Returns a dictionary containing:
        - session_id: Unique identifier for this simulation session
        - case_path: Path to the loaded case file
        - system_info: Basic information about the loaded system

        Example:
        {
            "session_id": "abc-123-def-456",
            "case_path": "ieee14/ieee14.xlsx",
            "system_info": {...}
        }
        """
        import gc
        from pathlib import Path

        system = None

        try:
            # Try to resolve as built-in case first
            full_path = MCPConfig.get_case_path(case_path)
            if full_path is None:
                # Try as absolute path
                full_path = case_path

            # Validate that the file exists before attempting load
            if not Path(full_path).exists():
                return {
                    "success": False,
                    "error": f"Case file not found: {case_path}. Path resolved to: {full_path}"
                }

            # Load the case
            system = andes.load(
                str(full_path),
                setup=setup,
                no_output=no_output,
                default_config=False,
            )

            if system is None:
                # Force garbage collection to clean up any partial state
                gc.collect()
                return {
                    "success": False,
                    "error": f"Failed to load case: {case_path}. The file may be corrupted or in an unsupported format."
                }

            # Create session
            session_manager = get_session_manager()
            session_id = session_manager.create_session(system, case_path)

            return {
                "success": True,
                "session_id": session_id,
                "case_path": case_path,
                "system_info": serialize_system_info(system),
            }

        except Exception as e:
            # Clean up the partial system if it was created
            if system is not None:
                del system

            # Force garbage collection to clean up any partial state
            gc.collect()

            return {
                "success": False,
                "error": f"Error loading case: {str(e)}"
            }

    @mcp.tool()
    def get_system_info(session_id: str) -> dict:
        """
        Get detailed information about a loaded system.

        Parameters:
        - session_id: Session identifier from load_case

        Returns a dictionary containing:
        - name: System name
        - case_path: Path to case file
        - models: Dictionary of model names and counts
        - dae_info: Information about differential-algebraic equations
        - config: System configuration

        Example:
        {
            "name": "IEEE 14-bus",
            "models": {"Bus": {"count": 14}, "PQ": {"count": 11}, ...},
            "dae_info": {"n_states": 0, "n_algebraic": 28},
            ...
        }
        """
        session_manager = get_session_manager()
        system = session_manager.get_system(session_id)

        if system is None:
            return {
                "success": False,
                "error": f"Session not found: {session_id}"
            }

        try:
            return {
                "success": True,
                "session_id": session_id,
                **serialize_system_info(system)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting system info: {str(e)}"
            }

    @mcp.tool()
    def list_sessions() -> dict:
        """
        List all active simulation sessions.

        Returns a dictionary containing:
        - sessions: List of active session metadata
        - count: Total number of active sessions

        Example:
        {
            "sessions": [
                {
                    "session_id": "abc-123",
                    "case_path": "ieee14/ieee14.xlsx",
                    "created_at": 1234567890.0,
                    "last_accessed": 1234567900.0
                },
                ...
            ],
            "count": 2
        }
        """
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions()

        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
        }

    @mcp.tool()
    def close_session(session_id: str) -> dict:
        """
        Close and remove a simulation session.

        Parameters:
        - session_id: Session identifier to close

        Returns a dictionary with:
        - success: True if session was closed, False otherwise
        - message: Status message
        """
        session_manager = get_session_manager()
        closed = session_manager.close_session(session_id)

        if closed:
            return {
                "success": True,
                "message": f"Session {session_id} closed successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Session not found: {session_id}"
            }
