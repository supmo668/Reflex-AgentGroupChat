"""Token manager for storing cancellation tokens outside of Reflex state."""

import logging
from typing import Dict, Optional
from autogen_core import CancellationToken
from autogen_agentchat.conditions import ExternalTermination

# Configure logging
logger = logging.getLogger(__name__)

class TokenManager:
    """Manages cancellation tokens and termination conditions outside of Reflex state.
    
    This class provides a singleton instance to store and retrieve cancellation tokens
    and termination conditions by session ID. This is necessary because Reflex state
    cannot directly store non-serializable objects like CancellationToken.
    """
    
    _instance = None
    
    def __new__(cls):
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(TokenManager, cls).__new__(cls)
            cls._instance._cancellation_tokens = {}
            cls._instance._termination_conditions = {}
        return cls._instance
    
    def store_cancellation_token(self, session_id: str, token: CancellationToken) -> None:
        """Store a cancellation token for a session.
        
        Args:
            session_id: The ID of the session.
            token: The cancellation token to store.
        """
        self._cancellation_tokens[session_id] = token
        logger.debug(f"Stored cancellation token for session {session_id}")
    
    def get_cancellation_token(self, session_id: str) -> Optional[CancellationToken]:
        """Get the cancellation token for a session.
        
        Args:
            session_id: The ID of the session.
            
        Returns:
            The cancellation token for the session, or None if not found.
        """
        token = self._cancellation_tokens.get(session_id)
        logger.debug(f"Retrieved cancellation token for session {session_id}: {token is not None}")
        return token
    
    def remove_cancellation_token(self, session_id: str) -> None:
        """Remove the cancellation token for a session.
        
        Args:
            session_id: The ID of the session.
        """
        if session_id in self._cancellation_tokens:
            del self._cancellation_tokens[session_id]
            logger.debug(f"Removed cancellation token for session {session_id}")
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a session by triggering its cancellation token.
        
        Args:
            session_id: The ID of the session to cancel.
            
        Returns:
            True if the session was cancelled, False otherwise.
        """
        token = self.get_cancellation_token(session_id)
        if token:
            token.cancel()
            logger.debug(f"Cancelled session {session_id}")
            return True
        return False
    
    def store_termination_condition(self, session_id: str, termination: ExternalTermination) -> None:
        """Store a termination condition for a session.
        
        Args:
            session_id: The ID of the session.
            termination: The termination condition to store.
        """
        self._termination_conditions[session_id] = termination
        logger.debug(f"Stored termination condition for session {session_id}")
    
    def get_termination_condition(self, session_id: str) -> Optional[ExternalTermination]:
        """Get the termination condition for a session.
        
        Args:
            session_id: The ID of the session.
            
        Returns:
            The termination condition for the session, or None if not found.
        """
        termination = self._termination_conditions.get(session_id)
        logger.debug(f"Retrieved termination condition for session {session_id}: {termination is not None}")
        return termination
    
    def remove_termination_condition(self, session_id: str) -> None:
        """Remove the termination condition for a session.
        
        Args:
            session_id: The ID of the session.
        """
        if session_id in self._termination_conditions:
            del self._termination_conditions[session_id]
            logger.debug(f"Removed termination condition for session {session_id}")
    
    def terminate_session(self, session_id: str) -> bool:
        """Terminate a session by triggering its termination condition.
        
        Args:
            session_id: The ID of the session to terminate.
            
        Returns:
            True if the session was terminated, False otherwise.
        """
        termination = self.get_termination_condition(session_id)
        if termination:
            termination.set()
            logger.debug(f"Terminated session {session_id}")
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all stored tokens and conditions."""
        self._cancellation_tokens.clear()
        self._termination_conditions.clear()
        logger.debug("Cleared all tokens and conditions")


# Create a singleton instance
token_manager = TokenManager()
