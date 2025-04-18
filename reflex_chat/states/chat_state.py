import logging
from typing import Optional, Dict, Literal, List
import asyncio
from uuid import uuid4

import reflex as rx
import yaml
import aiofiles

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
from autogen_agentchat.conditions import ExternalTermination
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient

from reflex_chat.config import BOTTOM_ELEMENT_ID
from reflex_chat.utils import token_manager

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MODEL_CONFIG_PATH = "model_config.yaml"
STATE_PATH = "team_state.json"
HISTORY_PATH = "team_history.json"

class Participant(rx.Base):
    """A participant in the chat."""
    name: str
    role: str = "character"
    system_message: str
    color: str


class Message(rx.Base):
    """Message model for chat interactions."""
    source: str
    models_usage: Optional[dict] = None
    metadata: dict = {}
    content: str
    type: Literal["TextMessage"] = "TextMessage"


# Message class is now the primary message representation
class ChatSession(rx.Base):
    """A chat session with a unique ID and messages."""
    id: str
    name: str
    messages: list[Message] = []
    is_initialized: bool = False
    submitted_message: str = ""
    initial_message: str = ""
    team_state: Dict[str, Dict[str, str]] = {}


class ChatState(rx.State):
    """The chat state."""
    
    # Chat sessions
    chat_sessions: Dict[str, ChatSession] = {}
    current_chat_id: str = ""
    show_modal: bool = False
    new_chat_name: str = ""
    is_processing: bool = False
    # Current message being typed
    user_message: str = ""
    # Scroll anchor
    scroll_flag: bool = False
    sidebar_open: bool = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create initial session if needed
        if not self.chat_sessions:
            initial_session = ChatSession(id=str(uuid4()), name="New Chat")
            self.chat_sessions = {initial_session.id: initial_session}
            self.current_chat_id = initial_session.id

    @rx.var
    def has_messages(self) -> bool:
        """Check if there are messages in the current session."""
        return self.current_session and len(self.messages) > 0
    
    @rx.var
    def can_send_message(self) -> bool:
        """Check if a message can be sent.
        Can send if:
        1. There's a non-empty message
        2. It's the user's turn (not processing and either not initialized or input requested)
        """
        allow_input = not self.is_processing or (not self.current_session.is_initialized and not self.is_processing)
        return self.has_messages and allow_input
        
    @rx.var
    def input_placeholder(self) -> str:
        """Get the appropriate placeholder text for the input field."""
        if not self.current_session:
            return "Type something..."
            
        # Show different placeholder based on whether the chat is initialized
        if not self.current_session.is_initialized:
            return "Kick-off with the topic of interest"
        else:
            return "Message to group..."
    
    @rx.var
    def submit_button_text(self) -> str:
        """Get the appropriate text for the submit button."""
        if not self.current_session:
            return "Start Chat"
            
        # Show different button text based on whether the chat is initialized
        if not self.current_session.is_initialized:
            return "Submit Topic & Start Chat"
        else:
            return "Send"
            
    @rx.var
    def submit_button_color(self) -> str:
        """Get the appropriate color for the submit button."""
        if not self.current_session or not self.current_session.is_initialized:
            return "green"
        else:
            return "violet"
    
    @rx.var
    def session_list(self) -> List[ChatSession]:
        """Get the list of chat sessions."""
        return list(self.chat_sessions.values())
    
    @rx.var
    def current_session(self) -> Optional[ChatSession]:
        """Get the current chat session."""
        return self.chat_sessions.get(self.current_chat_id)
    
    @rx.var
    def messages(self) -> List[Message]:
        """Get the messages in the current session."""
        return self.current_session.messages if self.current_session else []
        
    @rx.var
    def message_count(self) -> int:
        """Get the number of messages in the current session."""
        return len(self.messages)
        
    @rx.var
    def chat_participants(self) -> List[Participant]:
        """Get the list of participants in the current chat.
        
        Returns:
            List of Participant objects.
        """
        return [
            Participant(name="assistant", system_message="You are a helpful assistant.", color="violet"),
            Participant(name="yoda", system_message="Repeat the same message in the tone of Yoda.", color="green")
        ]
        
    def _get_participant_color(self, name: str) -> str:
        """Get the color for a participant."""
        colors = {
            "assistant": "gray",
            "system": "blue",
            "admin": "amber",
            "user": "black"
        }
        return colors.get(name.lower(), "violet")
        
    @rx.var
    def current_chat_name(self) -> str:
        """Get the name of the current chat session."""
        return self.current_session.name if self.current_session else "No Chat"
        
    @rx.var
    def initial_chat_message(self) -> str:
        """Get the initial message that started the chat."""
        if not self.current_session or not self.current_session.initial_message:
            return ""
        return self.current_session.initial_message
    
    @rx.event
    def toggle_sidebar(self):
        self.sidebar_open = not self.sidebar_open
        
    @rx.event
    def set_user_message(self, message: str):
        """Set the current message.
        
        Args:
            message: The message to set.
        """
        self.user_message = message
    
    @rx.event
    def set_chat_title(self, title: str):
        """Set the title for a new chat.
        
        Args:
            title: The title to set.
        """
        self.new_chat_name = title
        
    @rx.event
    async def create_chat(self):
        """Create a new chat session."""
        # Create new session
        session = ChatSession(id=str(uuid4()), name=self.new_chat_name if self.new_chat_name else "Untitled")
        self.chat_sessions[session.id] = session
        self.current_chat_id = session.id
        
        # Reset UI state
        self.new_chat_name = ""
        self.show_modal = False
        
    @rx.event
    async def delete_chat(self, chat_id: str):
        """Delete a chat session.
        
        Args:
            chat_id: The ID of the chat session to delete.
        """
        logger.debug(f"Deleting chat: {chat_id}")
        
        # Find the chat session
        if chat_id not in self.chat_sessions:
            logger.error(f"Chat session not found: {chat_id}")
            return
            
        # Gracefully terminate any ongoing chat in the session being deleted
        logger.debug(f"Gracefully terminating chat in session being deleted: {chat_id}")
        # Use the token manager to terminate the session
        token_manager.terminate_session(chat_id)
        # Also cancel immediately if needed
        token_manager.cancel_session(chat_id)
        
        # Clean up tokens from the manager
        token_manager.remove_termination_condition(chat_id)
        token_manager.remove_cancellation_token(chat_id)
            
        # Create a new dict without the deleted session
        updated_sessions = {k: v for k, v in self.chat_sessions.items() if k != chat_id}
        self.chat_sessions = updated_sessions
        
        # If this was the current chat, switch to another one or clear
        if self.current_chat_id == chat_id:
            if self.chat_sessions:
                # Get the first key from the dictionary
                self.current_chat_id = next(iter(self.chat_sessions))
            else:
                self.current_chat_id = ""
                # Create a new session if we deleted the last one
                self.create_chat()
                
        logger.debug(f"Deleted chat: {chat_id}")
    
    @rx.event
    def open_modal(self):
        """Open the new chat modal."""
        self.show_modal = True
        self.new_chat_name = ""
        
    @rx.event
    def close_modal(self):
        """Close the new chat modal."""
        self.show_modal = False
        
    @rx.event
    def check_and_open_modal(self):
        """Check if we need to open the modal and open it if needed."""
        # If there are no chat sessions or no current chat, open the modal
        if not self.chat_sessions or not self.current_chat_id:
            self.open_modal()
    
    @rx.event
    async def switch_chat(self, chat_id: str):
        """Switch to a different chat session.
        
        Args:
            chat_id: The ID of the chat session to switch to.
        """
        logger.debug(f"Switching to chat: {chat_id}")
        
        # Verify the chat exists
        if chat_id not in self.chat_sessions:
            logger.error(f"Cannot switch to non-existent chat: {chat_id}")
            return
            
        # Do nothing if the chat_id is the same as the current chat_id
        if chat_id == self.current_chat_id:
            return
            
        # Gracefully terminate any ongoing chat in the current session
        if self.current_session:
            logger.debug(f"Gracefully terminating ongoing chat in session: {self.current_session.id}")
            # Use the token manager to terminate the session
            token_manager.terminate_session(self.current_session.id)
            # Also cancel immediately if needed
            token_manager.cancel_session(self.current_session.id)

        # Set as current chat
        self.current_chat_id = chat_id
        logger.debug(f"Switched to chat: {chat_id}")
    
    async def get_team(self) -> RoundRobinGroupChat:
        """Get or create the team of agents for the current session."""
        if not self.current_session:
            logger.error("No current session available")
            raise ValueError("No current session available")
            
        # Create external termination condition that can be triggered from outside
        termination = ExternalTermination()
        
        # Store the termination condition in the token manager
        token_manager.store_termination_condition(self.current_session.id, termination)
        
        async def get_user_input(prompt: str, cancellation_token=None) -> str:
            """Get input from the user through the UI.
            
            Args:
                prompt: The prompt to show to the user.
                cancellation_token: Ignored parameter, we use ExternalTermination instead.
            
            Returns:
                The user's input.
            """
            logger.debug(f"Getting user input with prompt: {prompt}")
            
            if not self.current_session:
                logger.error("No current session available in get_user_input")
                raise ValueError("No current session available")
            logger.debug("Input enabled, waiting for message")
            
            try:
                while True:
                    # Wait for a message from the current session
                    logger.debug("Waiting for message from current session")
                    message = None
                    
                    if self.current_session and self.current_session.submitted_message:
                        message = self.current_session.submitted_message
                        async with self:
                            self.current_session.submitted_message = None
                    
                    if message:  # Only return non-empty messages
                        logger.debug(f"Got valid user input: {message}")
                        async with self:
                            self.is_processing = True
                        return message
                        
                    # Check if the external termination was triggered
                    # Get the termination condition from the token manager
                    current_termination = token_manager.get_termination_condition(self.current_session.id)
                    if current_termination and current_termination.terminated:
                        logger.debug("Input cancelled due to session termination")
                        raise asyncio.CancelledError("Session terminated")
                        
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error getting user input: {str(e)}")
                
            # finally:
            #     # Always disable input if cancelled
            #     async with self:
            #         if cancellation_token and cancellation_token.is_cancelled:
            #             self.processing = False
            
        logger.debug("Getting team instance")
        # Load model config
        async with aiofiles.open(MODEL_CONFIG_PATH, "r") as file:
            model_config = yaml.safe_load(await file.read())
            logger.debug("Loaded model config")
        model_client = ChatCompletionClient.load_component(model_config)
        logger.debug("Created model client")
        
        # Create agents
        participants = [
            AssistantAgent(
                name=p.name,
                model_client=model_client,
                system_message=p.system_message,
            )
            for p in self.chat_participants
        ]
        participants.append(UserProxyAgent(
            name="user",
            input_func=get_user_input,
        ))
        # Create the team
        team = RoundRobinGroupChat(participants, termination_condition=termination)
        
        # Load state from current session if exists
        if self.current_session and self.current_session.team_state:
            logger.debug(f"Loading team state from session {self.current_session.id}")
            await team.load_state(self.current_session.team_state)
                
        # No need to load history as it's already in the session
                
        return team, termination

    @rx.event
    def on_message_input(self, value: str):
        """Handle message input changes.
        
        Args:
            value: The new message value.
        """
        self.user_message = value
    
    @rx.event
    def handle_message_submit(self):
        """Handle message submission based on session state."""
        if not self.current_session:
            return

        # Don't process empty messages
        if not self.user_message.strip() and self.current_session.is_initialized:
            return
            
        logger.debug(f"Handling message submit: {self.user_message}")
        
        # Decide whether to start a new chat or submit a message to existing chat
        if not self.current_session.is_initialized:
            # Start a new chat
            logger.debug("Starting new chat")
            return ChatState.start_chat
        else:
            # Submit message to existing chat
            logger.debug("Submitting message to existing chat")
            return ChatState.submit_message
    
    @rx.event
    async def submit_message(self):
        """Submit a message to the team."""            
        # Store the message in the current session for get_user_input
        self.current_session.submitted_message = self.user_message
        self.is_processing = True
        # Create and add user message to chat
        user_message = Message(
            source="user",
            content=self.user_message,
            type="TextMessage"
        )
        
        # Add message to current session and clear input
        self.add_message_to_current_session(user_message)
        self.user_message = ""

    def add_message_to_current_session(self, message: Message):
        """Add a message to the current session using proper state update patterns.
        
        Args:
            message: The message to add to the current session.
        """
        if not self.current_session:
            logger.error("Cannot add message: No current session available")
            return
        # # Create a new list with the new message to ensure Reflex detects the change
        # updated_messages = self.chat_sessions[self.current_chat_id].messages + [message]
        # Assign the new list back to trigger proper UI updates
        self.chat_sessions[self.current_chat_id].messages.append(message)
        self.scroll_flag = not self.scroll_flag  # Toggle to trigger reactivity

        logger.debug(f"Added message from {message.source}: {message.content[:min(30, len(message.content))]}...")
    
    @rx.event(background=True)
    async def start_chat(self):
        """Start a new chat with the AI team."""
        logger.debug("Starting new chat")
        
        if not self.current_session:
            logger.error("No current session available")
            return
            
        # Mark session as initialized and processing
        async with self:
            self.current_session.is_initialized = True
            self.is_processing = True
        
        try:
            # Get team instance
            team, termination = await self.get_team()
            logger.debug("Team initialized successfully")
            
            # Create initial message for the team using the user's input or a default
            initial_content = self.user_message.strip() if self.user_message.strip() else "Let's start a conversation"
            # Store the initial message in the session
            self.current_session.initial_message = initial_content
            request = TextMessage(content=initial_content, source="user")
            
            # Create a cancellation token for immediate cancellation if needed
            cancellation_token = CancellationToken()
            # Store it in the token manager
            token_manager.store_cancellation_token(self.current_session.id, cancellation_token)
            
            # Use both the termination condition (via team config) and cancellation token
            stream = team.run_stream(task=request, cancellation_token=cancellation_token)
            
            async for message in stream:
                logger.debug(f"Got message: {message}")
                if isinstance(message, TaskResult):
                    logger.debug("Skipping TaskResult message")
                    continue
                if isinstance(message, UserInputRequestedEvent):
                    logger.debug("Waiting for user input")
                    # Enable input and wait
                    async with self:
                        self.is_processing = False
                    continue
                    
                # Extract content and source from the message
                content = getattr(message, 'content', str(message))
                source = getattr(message, 'source', 'system')
                
                # Add to current session
                async with self:
                    new_message = Message(content=content, source=source, type="TextMessage")
                    self.add_message_to_current_session(new_message)
                    logger.debug(f"Added message from {source}: {content[:30]}...")
            
            # Save team state
            state = await team.save_state()
            # Store the state in the current session
            if self.current_session and state:
                self.current_session.team_state = state
                logger.debug(f"Saved team state for session {self.current_session.id}")
            termination.cancel()
            logger.debug("Got team state")
            
            # Store the state in the session
            async with self:
                self.current_session.team_state = state
                
        except Exception as e:
            logger.error(f"Error starting chat: {str(e)}")
            async with self:
                # Add error message to chat
                error_message = Message(content=f"Failed to initialize chat: {str(e)}", source="system", type="TextMessage")
                self.add_message_to_current_session(error_message)
                self.is_processing = False
            
        finally:
            # Reset processing flag
            async with self:
                self.is_processing = False
                
        logger.debug("Chat initialization completed")
    
    async def scroll_to_bottom(self):
        """Scroll the chat container to the bottom."""
        try:
            # yield rx.call_script(
            #     """
            #     const container = document.getElementById('chat-container');
            #     if (container) {
            #         container.scrollTop = container.scrollHeight;
            #     } else {
            #         console.warn('Chat container not found');
            #     }
            #     """
            # )
            yield rx.call_script(f"document.getElementById('{BOTTOM_ELEMENT_ID}').scrollIntoView()")
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {str(e)}")
