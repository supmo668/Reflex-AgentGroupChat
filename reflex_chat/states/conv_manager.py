import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages AutoGen conversations and synchronization primitives"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ConversationManager()
        return cls._instance
    
    def __init__(self):
        self._conversations = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
    
    async def start_cleanup_task(self, interval_minutes: int = 10, max_age_minutes: int = 60):
        """Start periodic cleanup of stale conversations"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_minutes * 60)
                    await self.cleanup_stale_conversations(max_age_minutes)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def register_conversation(self, conversation_id: str) -> None:
        """Register a new conversation or reset an existing one"""
        async with self._lock:
            self._conversations[conversation_id] = {
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "input_event": asyncio.Event(),
                "pending_input": None,
                "team": None,
                "cancel_token": None
            }
    
    async def set_team(self, conversation_id: str, team: Any, cancel_token: Any) -> None:
        """Set the AutoGen team for a conversation"""
        async with self._lock:
            if conversation_id in self._conversations:
                self._conversations[conversation_id]["team"] = team
                self._conversations[conversation_id]["cancel_token"] = cancel_token
                self._conversations[conversation_id]["last_active"] = datetime.now()
    
    async def get_team(self, conversation_id: str) -> Optional[Any]:
        """Get the AutoGen team for a conversation"""
        async with self._lock:
            if conversation_id in self._conversations:
                self._conversations[conversation_id]["last_active"] = datetime.now()
                return self._conversations[conversation_id]["team"]
            return None
    
    async def get_cancel_token(self, conversation_id: str) -> Optional[Any]:
        """Get the cancellation token for a conversation"""
        async with self._lock:
            if conversation_id in self._conversations:
                return self._conversations[conversation_id]["cancel_token"]
            return None
    
    async def set_pending_input(self, conversation_id: str, input_text: str) -> bool:
        """Set pending input for a conversation and signal the event"""
        async with self._lock:
            if conversation_id in self._conversations:
                self._conversations[conversation_id]["pending_input"] = input_text
                self._conversations[conversation_id]["last_active"] = datetime.now()
                self._conversations[conversation_id]["input_event"].set()
                return True
            return False
    
    async def wait_for_input(self, conversation_id: str, timeout: int = 300) -> Optional[str]:
        """Wait for input for a conversation with timeout"""
        conv_data = None
        
        async with self._lock:
            if conversation_id not in self._conversations:
                return None
            
            # Clear the event in case it was previously set
            self._conversations[conversation_id]["input_event"].clear()
            conv_data = self._conversations[conversation_id]
        
        # If already has pending input, return it immediately
        if conv_data["pending_input"] is not None:
            input_text = conv_data["pending_input"]
            
            async with self._lock:
                self._conversations[conversation_id]["pending_input"] = None
                self._conversations[conversation_id]["last_active"] = datetime.now()
            
            return input_text
        
        try:
            # Wait for the event with timeout
            await asyncio.wait_for(conv_data["input_event"].wait(), timeout=timeout)
            
            # Get the input
            async with self._lock:
                if conversation_id not in self._conversations:
                    return None
                
                input_text = self._conversations[conversation_id]["pending_input"]
                self._conversations[conversation_id]["pending_input"] = None
                self._conversations[conversation_id]["last_active"] = datetime.now()
            
            return input_text
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for input in conversation {conversation_id}")
            return None
    
    async def cancel_conversation(self, conversation_id: str) -> bool:
        """Cancel a conversation"""
        async with self._lock:
            if conversation_id in self._conversations:
                if self._conversations[conversation_id]["cancel_token"] is not None:
                    self._conversations[conversation_id]["cancel_token"].cancel()
                
                # Signal any waiting input to unblock
                self._conversations[conversation_id]["input_event"].set()
                self._conversations[conversation_id]["last_active"] = datetime.now()
                return True
            return False
    
    async def remove_conversation(self, conversation_id: str) -> bool:
        """Remove a conversation"""
        async with self._lock:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                return True
            return False
    
    async def cleanup_stale_conversations(self, max_age_minutes: int = 60) -> int:
        """Clean up stale conversations"""
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
        count = 0
        
        async with self._lock:
            for conv_id in list(self._conversations.keys()):
                if self._conversations[conv_id]["last_active"] < cutoff:
                    # Cancel conversation if active
                    if self._conversations[conv_id]["cancel_token"] is not None:
                        self._conversations[conv_id]["cancel_token"].cancel()
                    
                    del self._conversations[conv_id]
                    count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} stale conversations")
        
        return count