from typing import Optional, List
from ..utils import get_session_manager, serialize_pflow_results, serialize_tds_results
from ..config import MCPConfig


def register_results_tools(mcp):
    """Register results tools with the MCP server"""

    @mcp.tool()
    def get_pflow_results(session_id: str) -> dict:
        """
        Get power flow calculation results.

        Parameters:
        - session_id: Session identifier from load_case

        Returns a dictionary containing:
        - success: True if results available
        - converged: Power flow convergence status
        - iterations: Number of iterations
        - buses: Bus voltage magnitudes and angles
        - generators: Generator real and reactive power outputs

        Example:
        {
            "success": True,
            "converged": True,
            "iterations": 4,
            "buses": {
                "idx": [1, 2, 3, ...],
                "voltage": [1.06, 1.045, ...],
                "angle": [0.0, -4.98, ...]
            },
            "generators": {...}
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
            if not hasattr(system, 'PFlow'):
                return {
                    "success": False,
                    "error": "Power flow routine not available"
                }

            results = serialize_pflow_results(system)
            results["success"] = True
            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving power flow results: {str(e)}"
            }

    @mcp.tool()
    def get_tds_results(
        session_id: str,
        variables: Optional[List[str]] = None,
        max_points: Optional[int] = None
    ) -> dict:
        """
        Get time-domain simulation results.

        Parameters:
        - session_id: Session identifier from load_case
        - variables: List of specific variable names to retrieve (optional)
                    If None, returns all state variables
        - max_points: Maximum number of data points to return (optional)
                     If provided and exceeded, data will be downsampled

        Returns a dictionary containing:
        - success: True if results available
        - time: Array of time points
        - n_points: Number of time points
        - variables: Dictionary mapping variable names to their time series data
        - downsampled: True if data was downsampled

        Example:
        {
            "success": True,
            "time": [0.0, 0.0333, 0.0667, ...],
            "n_points": 600,
            "variables": {
                "omega_GENROU_1": [1.0, 1.0001, ...],
                "delta_GENROU_1": [0.0, 0.001, ...]
            },
            "downsampled": False
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
            if not hasattr(system, 'TDS'):
                return {
                    "success": False,
                    "error": "Time-domain simulation routine not available"
                }

            if max_points is None:
                max_points = MCPConfig.MAX_RESULT_POINTS

            results = serialize_tds_results(system, variables=variables, max_points=max_points)
            results["success"] = True
            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving TDS results: {str(e)}"
            }

    @mcp.tool()
    def list_tds_variables(session_id: str) -> dict:
        """
        List all available variables from time-domain simulation.

        Parameters:
        - session_id: Session identifier from load_case

        Returns a dictionary containing:
        - success: True if variables available
        - state_variables: List of state variable names (x)
        - algebraic_variables: List of algebraic variable names (y)
        - n_states: Number of state variables
        - n_algebraic: Number of algebraic variables

        Example:
        {
            "success": True,
            "state_variables": ["omega_GENROU_1", "delta_GENROU_1", ...],
            "algebraic_variables": ["v_Bus_1", "a_Bus_1", ...],
            "n_states": 20,
            "n_algebraic": 28
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
            if not system.TDS.initialized:
                return {
                    "success": False,
                    "error": "Time-domain simulation not initialized"
                }

            return {
                "success": True,
                "state_variables": system.dae.x_name,
                "algebraic_variables": system.dae.y_name,
                "n_states": len(system.dae.x_name),
                "n_algebraic": len(system.dae.y_name),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing variables: {str(e)}"
            }
