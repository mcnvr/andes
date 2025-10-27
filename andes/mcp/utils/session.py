import time
import uuid
from typing import Dict, Optional
from andes.system import System


class Session:
    """
    Represents a single ANDES simulation session.
    """

    def __init__(self, session_id: str, system: System, case_path: str):
        self.session_id = session_id
        self.system = system
        self.case_path = case_path
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.metadata = {}

    def touch(self):
        """Update last accessed timestamp"""
        self.last_accessed = time.time()

    def is_expired(self, timeout: int) -> bool:
        """Check if session has expired"""
        return (time.time() - self.last_accessed) > timeout


class SessionManager:
    """
    Manages multiple ANDES System instances with session lifecycle.
    """

    def __init__(self, max_sessions: int = 100, timeout: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.timeout = timeout

    def create_session(self, system: System, case_path: str) -> str:
        """
        Create a new session with an ANDES System instance.

        Parameters
        ----------
        system : System
            ANDES System object
        case_path : str
            Path to the case file that was loaded

        Returns
        -------
        str
            Unique session ID
        """
        # Clean up expired sessions before creating new one
        self._cleanup_expired()

        # Enforce max sessions limit
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest session
            oldest_id = min(self.sessions.keys(),
                            key=lambda k: self.sessions[k].last_accessed)
            del self.sessions[oldest_id]

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session = Session(session_id, system, case_path)
        self.sessions[session_id] = session

        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID and update its last accessed time.

        Parameters
        ----------
        session_id : str
            Session identifier

        Returns
        -------
        Optional[Session]
            Session object if found and not expired, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired(self.timeout):
                del self.sessions[session_id]
                return None
            session.touch()
        return session

    def get_system(self, session_id: str) -> Optional[System]:
        """
        Retrieve the ANDES System object for a session.

        Parameters
        ----------
        session_id : str
            Session identifier

        Returns
        -------
        Optional[System]
            ANDES System object if session exists, None otherwise
        """
        session = self.get_session(session_id)
        return session.system if session else None

    def close_session(self, session_id: str) -> bool:
        """
        Close and remove a session.

        Parameters
        ----------
        session_id : str
            Session identifier

        Returns
        -------
        bool
            True if session was removed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> list[dict]:
        """
        List all active sessions.

        Returns
        -------
        list[dict]
            List of session metadata
        """
        self._cleanup_expired()
        return [
            {
                "session_id": sid,
                "case_path": session.case_path,
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
            }
            for sid, session in self.sessions.items()
        ]

    def _cleanup_expired(self):
        """Remove expired sessions"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.timeout)
        ]
        for sid in expired:
            del self.sessions[sid]


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get the global SessionManager instance (singleton pattern).

    Returns
    -------
    SessionManager
        The global session manager
    """
    global _session_manager
    if _session_manager is None:
        from ..config import MCPConfig
        _session_manager = SessionManager(
            max_sessions=MCPConfig.MAX_SESSIONS,
            timeout=MCPConfig.SESSION_TIMEOUT
        )
    return _session_manager
