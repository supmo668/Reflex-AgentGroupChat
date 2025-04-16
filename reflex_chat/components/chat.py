import reflex as rx
import reflex_chakra as rc
import logging

from reflex_chat.components import loading_icon
from reflex_chat.states.chat_state import ChatState, Message

# Configure logging
logger = logging.getLogger(__name__)

message_style = dict(
    display="inline-block",
    padding="1em",
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"]
)


def message(msg: Message) -> rx.Component:
    """A single message.

    Args:
        msg: The message to display.

    Returns:
        A component displaying the message.
    """
    # Define source-specific styling
    source_styles = {
        "user": {
            "bg_color": "mauve",
            "text_color": "mauve",
            "align": "right",
            "avatar": "👤"
        },
        "assistant": {
            "bg_color": "violet",
            "text_color": "violet",
            "align": "left",
            "avatar": "🤖"
        },
        "system": {
            "bg_color": "blue",
            "text_color": "blue",
            "align": "left",
            "avatar": "ℹ️"
        },
        "yoda": {
            "bg_color": "green",
            "text_color": "green",
            "align": "left",
            "avatar": "🧙"
        },
        "admin": {
            "bg_color": "amber",
            "text_color": "amber",
            "align": "center",
            "avatar": "🔔"
        }
    }
    
    # Convert source to lowercase for case-insensitive matching
    source = msg.source.lower()    
    # Get style for this message source or use default
    style = source_styles.get(source, source_styles["system"])
    
    return rx.hstack(
        rx.box(
            style["avatar"],
            font_size="1.5em",
            margin_top="0.5em",
            display=rx.cond(style["align"] == "right", "none", "block"),
        ),
        rx.vstack(
            rx.text(
                # Simplified conditional rendering for source name
                rx.cond(
                    source == "user", "User",
                    rx.cond(source == "system", "System",
                           # For all other sources (AI participants), show the capitalized source name
                           source.upper())
                ),
                font_size="0.8em",
                color=rx.color(style["text_color"], 10),
                align_self=style["align"],
                font_weight="bold",
            ),
            rx.box(
                rx.markdown(
                    msg.content,
                    background_color=rx.color(style["bg_color"], 4),
                    color=rx.color(style["text_color"], 12),
                    **message_style,
                ),
                text_align=style["align"],
            ),
            width="100%",
            spacing="0",
            align_items=style["align"],
        ),
        rx.box(
            style["avatar"],
            font_size="1.5em",
            margin_top="0.5em",
            display=rx.cond(style["align"] == "left", "none", "block"),
        ),
        width="100%",
        justify_content=rx.cond(
            style["align"] == "right", "flex-end",
            rx.cond(style["align"] == "center", "center", "flex-start")
        ),
        align_items="flex-start",
        padding_y="0.5em",
    )


def chat() -> rx.Component:
    """The main chat component."""
    return rx.vstack(
        rx.box(
            rx.cond(
                ChatState.current_session,  # First check if we have a session
                rx.cond(
                    ChatState.has_messages,  # Then check if there are messages
                    rx.foreach(
                        ChatState.messages,
                        message
                    ),
                    # Show welcome message if no messages
                    rx.center(
                        rx.vstack(
                            rx.heading("Welcome to Multi-Agent Chat"),
                            rx.text("Type a message below to start chatting with AI agents."),
                            padding="2em",
                            spacing="4",
                            text_align="center",
                            color=rx.color("mauve", 11),
                        ),
                        height="100%",
                    )
                ),
                # No session available
                rx.center(
                    rx.vstack(
                        rx.heading("No Chat Session"),
                        rx.text("Create a new chat to get started."),
                        padding="2em",
                        spacing="4",
                        text_align="center",
                        color=rx.color("mauve", 11),
                    ),
                    height="100%",
                )
            ),
            width="100%",
            overflow_y="auto",  # Enable vertical scrolling
            id="chat-container", # Add an ID to reference
            min_height="300px",
            height="100%",
        ),
        py="8",
        flex="1", 
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
        on_mount=ChatState.scroll_to_bottom,  # Add scroll on mount
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rc.form(
                rc.form_control(
                    rx.hstack(
                        rx.input(
                            rx.input.slot(
                                rx.tooltip(
                                    rx.icon("info", size=18),
                                    content="Enter a message to chat.",
                                )
                            ),
                            placeholder=ChatState.input_placeholder,
                            id="message",
                            value=ChatState.user_message,
                            on_change=ChatState.set_user_message,
                            width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        ),
                        rx.button(
                            rx.cond(
                                ChatState.current_session.is_processing,
                                loading_icon(height="1em"),
                                rx.text(ChatState.submit_button_text),
                            ),
                            type="submit",
                            color_scheme=ChatState.submit_button_color,
                            is_disabled=~ChatState.can_send_message,
                        ),
                        align_items="center",
                    ),
                    is_disabled=~ChatState.can_send_message,
                ),
                on_submit=ChatState.handle_message_submit,
                reset_on_submit=False,
            ),
            rx.text(
                "AI assistants may return factually incorrect or misleading responses. Use discretion.",
                text_align="center",
                font_size=".75em",
                color=rx.color("mauve", 10),
            ),
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )
