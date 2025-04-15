import os
import json
import logging
from typing import Any, Optional, Callable, Awaitable
import asyncio

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

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Constants
MODEL_CONFIG_PATH = "model_config.yaml"
STATE_PATH = "team_state.json"
HISTORY_PATH = "team_history.json"

class QA(rx.Base):
    """A question and answer pair."""
    content: str
    source: str


class ChatState(rx.State):
    """The chat state."""
    
    # The list of messages in the current chat
    messages: list[QA] = []
    
    # Whether we are processing a message
    processing: bool = False
    chat_ongoing: bool = False
    # The current message being typed
    current_message: str = ""
    submitted_message: Optional[str] = None
    
    # The team state as a dictionary
    team_state: dict = {}

    async def get_team(self) -> RoundRobinGroupChat:
        """Get or create the team of agents."""
        termination = ExternalTermination()
        async def get_user_input(prompt: str, cancellation_token: Optional[CancellationToken] = None) -> str:
            """Get input from the user through the UI.
            
            Args:
                prompt: The prompt to show to the user.
                cancellation_token: Optional token to cancel the operation.
            
            Returns:
                The user's input.
            """
            logger.debug(f"Getting user input with prompt: {prompt}")
            
            async with self:
                # Enable input and show prompt
                self.processing = False
                logger.debug("Input enabled, waiting for message")
            
            try:
                while True:
                    # Wait for a message from the queue
                    logger.debug("Waiting for message from queue")
                    message = None
                    if self.submitted_message:
                        message = self.submitted_message
                        async with self:
                            self.submitted_message = None
                    if message:  # Only return non-empty messages
                        logger.debug(f"Got valid user input: {message}")
                        async with self:
                            self.processing = True
                        return message
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
        assistant = AssistantAgent(
            name="assistant",
            model_client=model_client,
            system_message="You are a helpful assistant.",
        )
        
        yoda = AssistantAgent(
            name="yoda",
            model_client=model_client,
            system_message="Repeat the same message in the tone of Yoda.",
        )
        
        # Create user proxy with our custom input function
        user_proxy = UserProxyAgent(
            name="user",
            input_func=get_user_input,
        )
        
        # Create the team
        team = RoundRobinGroupChat([assistant, yoda, user_proxy], termination_condition=termination)
        
        # Load state if exists
        if self.team_state:
            await team.load_state(self.team_state)
        elif os.path.exists(STATE_PATH):
            async with aiofiles.open(STATE_PATH, "r") as file:
                state = json.loads(await file.read())
                await team.load_state(state)
                self.team_state = state
                
        # Load history if exists
        if not self.messages and os.path.exists(HISTORY_PATH):
            async with aiofiles.open(HISTORY_PATH, "r") as file:
                history = json.loads(await file.read())
                self.messages = [QA(**msg) for msg in history]
                
        return team, termination

    def on_message_input(self, value: str):
        """Handle message input changes.
        
        Args:
            value: The new message value.
        """
        self.current_message = value
    
    @rx.event
    def submit_message(self):
        """Submit a message to the team."""
        self.submitted_message = self.current_message
        self.current_message = ""

    @rx.event(background=True)
    async def start_chat(self):
        """Send a message to the team."""
        logger.debug("Starting send_message")
        
        # Put message in queue for get_user_input
        async with self:
            # Set processing flag
            self.processing = True
            # Add user message to chat
            user_message = QA(content="Let's talk about sci-fi movies", source="admin")
            logger.debug(f"Added user message: {user_message}")
        
        try:
            # Save history
            async with aiofiles.open(HISTORY_PATH, "w") as file:
                await file.write(json.dumps([msg.dict() for msg in self.messages]))
                logger.debug("Saved chat history")
                
            # Get team and process message
            team, termination = await self.get_team()
            logger.debug("Got team instance")
            
            # Create message for the team
            request = TextMessage(content=self.current_message, source="user")
            stream = team.run_stream(task=request)
            
            async for message in stream:
                if isinstance(message, TaskResult):
                    logger.debug("Skipping TaskResult message")
                    continue
                
                logger.debug(f"Got message: {message}")
                
                if isinstance(message, UserInputRequestedEvent):
                    logger.debug("Waiting for user input")
                    # Enable input and wait
                    async with self:
                        self.processing = False
                    # The get_user_input function will be called by the UserProxyAgent
                    continue
                    
                async with self:
                    agent_message = QA(content=message.content, source=message.source)
                    self.messages.append(agent_message)
                    logger.debug(f"Added agent message: {agent_message}")
                
                # Save history
                async with aiofiles.open(HISTORY_PATH, "w") as file:
                    await file.write(json.dumps([msg.dict() for msg in self.messages]))
                    logger.debug("Saved updated chat history")
            
            # Save team state
            state = await team.save_state()
            termination.cancel()
            logger.debug("Got team state")
            
            async with self:
                self.team_state = state
            
            async with aiofiles.open(STATE_PATH, "w") as file:
                await file.write(json.dumps(self.team_state))
                logger.debug("Saved team state to file")
                
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            async with self:
                # Add error message to chat
                error_message = QA(
                    content=f"An error occurred: {str(e)}",
                    source="system"
                )
                self.messages.append(error_message)
            
        finally:
            async with self:
                # Reset processing flag if not waiting for input
                # if not any(isinstance(msg, UserInputRequestedEvent) for msg in self.messages):
                self.processing = False
                
            logger.debug("Finished send_message")

    @rx.event(background=True)
    async def scroll_to_bottom(self):
        """Scroll the chat container to the bottom."""
        logger.debug("Scrolling chat container to bottom")
        try:
            yield rx.call_script(
                """
                const container = document.getElementById('chat-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                    console.log('Scrolled chat container to bottom');
                } else {
                    console.warn('Chat container not found');
                }
                """
            )
            logger.debug("Scroll script executed")
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {str(e)}")
