from typing import Optional
from ..utils import get_session_manager, serialize_pflow_results, serialize_tds_results
from ..config import MCPConfig


def register_analysis_tools(mcp):
    """Register analysis tools with the MCP server"""

    @mcp.tool()
    def run_power_flow(
        session_id: str,
        tol: Optional[float] = None,
        max_iter: Optional[int] = None,
        method: Optional[str] = None
    ) -> dict:
        """
        Run power flow calculation on a loaded system.

        Parameters:
        - session_id: Session identifier from load_case
        - tol: Convergence tolerance (optional, default: 1e-6)
        - max_iter: Maximum iterations (optional, default: 25)
        - method: Solution method - "NR", "dishonest", or "NK" (optional, default: "NR")

        Returns a dictionary containing:
        - success: True if power flow converged
        - converged: Convergence status
        - iterations: Number of iterations
        - exec_time: Execution time in seconds
        - buses: Bus voltage and angle results
        - generators: Generator P and Q outputs (if available)

        Example:
        {
            "success": True,
            "converged": True,
            "iterations": 4,
            "exec_time": 0.023,
            "buses": {"idx": [...], "voltage": [...], "angle": [...]},
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
            # Apply config overrides if provided
            if tol is not None:
                system.PFlow.config.tol = float(tol)
            if max_iter is not None:
                system.PFlow.config.max_iter = int(max_iter)
            if method is not None:
                system.PFlow.config.method = method

            # Run power flow
            converged = system.PFlow.run()

            # Serialize results
            results = serialize_pflow_results(system)
            results["success"] = True

            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Error running power flow: {str(e)}"
            }

    @mcp.tool()
    def run_time_domain(
        session_id: str,
        tf: Optional[float] = None,
        tstep: Optional[float] = None,
        tol: Optional[float] = None,
        method: Optional[str] = None
    ) -> dict:
        """
        Run time-domain simulation on a loaded system.

        Parameters:
        - session_id: Session identifier from load_case
        - tf: Simulation end time in seconds (optional, default: 20.0)
        - tstep: Integration time step in seconds (optional, default: 1/30)
        - tol: Convergence tolerance (optional, default: 1e-4)
        - method: Integration method - "trapezoid" (optional, default: "trapezoid")

        Returns a dictionary containing:
        - success: True if simulation completed
        - converged: True if simulation didn't encounter errors
        - exec_time: Execution time in seconds
        - time_range: [start_time, end_time] of simulation
        - n_points: Number of data points stored

        Note: Use get_tds_results to retrieve the actual time series data.

        Example:
        {
            "success": True,
            "converged": True,
            "exec_time": 1.234,
            "time_range": [0.0, 20.0],
            "n_points": 600
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
            # Ensure power flow has been run
            if not system.PFlow.converged:
                return {
                    "success": False,
                    "error": "Power flow must be run successfully before time-domain simulation"
                }

            # Apply config overrides
            if tf is not None:
                system.TDS.config.tf = float(tf)
            else:
                system.TDS.config.tf = MCPConfig.DEFAULT_TDS_TF

            if tstep is not None:
                system.TDS.config.tstep = float(tstep)
            if tol is not None:
                system.TDS.config.tol = float(tol)
            if method is not None:
                system.TDS.set_method(method)

            # Run TDS
            success = system.TDS.run()

            return {
                "success": True,
                "converged": success and not system.TDS.busted,
                "exec_time": float(system.TDS.exec_time) if hasattr(system.TDS, 'exec_time') else None,
                "time_range": [float(system.TDS.config.t0), float(system.TDS.config.tf)],
                "n_points": len(system.dae.ts.t),
                "message": "Time-domain simulation completed. Use get_tds_results to retrieve data."
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error running time-domain simulation: {str(e)}"
            }

    @mcp.tool()
    def run_eigenvalue(session_id: str) -> dict:
        """
        Run eigenvalue analysis on a loaded system.

        Parameters:
        - session_id: Session identifier from load_case

        Returns a dictionary containing:
        - success: True if analysis completed
        - n_eigenvalues: Number of eigenvalues computed
        - eigenvalues: Real and imaginary parts of eigenvalues

        Example:
        {
            "success": True,
            "n_eigenvalues": 20,
            "eigenvalues": {
                "real": [-0.1, -0.2, ...],
                "imag": [1.5, 2.3, ...]
            }
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
            # Ensure power flow has been run
            if not system.PFlow.converged:
                return {
                    "success": False,
                    "error": "Power flow must be run successfully before eigenvalue analysis"
                }

            # Run eigenvalue analysis
            system.EIG.run()

            # Import serialization here to avoid circular import
            from ..utils.serialization import serialize_eig_results
            results = serialize_eig_results(system)
            results["success"] = True

            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Error running eigenvalue analysis: {str(e)}"
            }
