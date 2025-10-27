import os
from pathlib import Path
from typing import Optional


class MCPConfig:
    """Configuration for the MCP server"""

    # Server metadata
    NAME = "andes-mcp-server"
    VERSION = "0.1.0"
    DESCRIPTION = "Model Context Protocol server for ANDES power system simulation"

    # Session management
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    MAX_SESSIONS = 100

    # File paths
    ANDES_ROOT = Path(__file__).parent.parent
    CASES_DIR = ANDES_ROOT / "cases"

    # Simulation defaults
    DEFAULT_TDS_TF = 20.0  # Default simulation end time
    DEFAULT_TDS_TSTEP = 1/30  # Default time step

    # Output settings
    MAX_RESULT_POINTS = 10000  # Maximum data points to return in a single query
    DEFAULT_OUTPUT_FORMAT = "json"

    @classmethod
    def get_case_path(cls, case_name: str) -> Optional[Path]:
        """
        Get the full path to a test case file.

        Parameters
        ----------
        case_name : str
            Relative path to case file (e.g., "ieee14/ieee14.xlsx")

        Returns
        -------
        Optional[Path]
            Full path to case file if it exists, None otherwise
        """
        case_path = cls.CASES_DIR / case_name
        return case_path if case_path.exists() else None

    @classmethod
    def list_all_cases(cls) -> list[str]:
        """
        List all available test case files.

        Returns
        -------
        list[str]
            List of relative paths to test case files
        """
        cases = []
        if cls.CASES_DIR.exists():
            for case_file in cls.CASES_DIR.rglob("*.xlsx"):
                rel_path = case_file.relative_to(cls.CASES_DIR)
                cases.append(str(rel_path).replace("\\", "/"))
            for case_file in cls.CASES_DIR.rglob("*.raw"):
                rel_path = case_file.relative_to(cls.CASES_DIR)
                cases.append(str(rel_path).replace("\\", "/"))
        return sorted(cases)
