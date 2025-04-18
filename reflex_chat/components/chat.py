import reflex as rx
import reflex_chakra as rc
import logging

from reflex_chat.components import loading_icon
from reflex_chat.states.chat_state import ChatState, Message, Participant
from reflex_chat.components.transcribe import transcribe_button

from reflex_chat.config import BOTTOM_ELEMENT_ID
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
        "participant": {
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

def chat_messages() -> rx.Component:
    return rx.vstack(
        rx.cond(
            ChatState.current_session,
            rx.cond(
                ChatState.has_messages,  # Then check if there are messages
                rx.foreach(ChatState.messages, message),
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
                ),
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
            ),
        ),
        rx.el.div(id=BOTTOM_ELEMENT_ID, style={"height": "1px"}),  # Hidden anchor
    )

def chat_stats_bar() -> rx.Component:
    def render_participant(participant: rx.Var[Participant]) -> rx.Component:
        return rx.badge(
            participant.name,
            color_scheme=participant.color,
            margin_right="1",
            variant="soft",
        )
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.icon("circle", size=18, color=rx.color("mauve", 10)),
                rx.text("Topic:", size="2", color=rx.color("mauve", 10)),
                rx.text(
                    ChatState.initial_chat_message,
                    font_style="italic",
                    color=rx.color("mauve", 11),
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                spacing="2",
                align_items="center",
                flex_grow=1,
                min_width="0",
            ),
            width="100%",
            justify_content="space-between",
            background_color=rx.color("mauve", 2),
            border_radius="md",
            border=f"1px solid {rx.color('mauve', 4)}",
            box_shadow="sm",
            align_items="center",
        ),
        rx.hstack(
            rx.hstack(
                rx.icon("message_circle", size=18, color=rx.color("violet", 9)),
                rx.text(f"Messages: {ChatState.message_count}", size="2", color=rx.color("mauve", 10)),
                spacing="2",
                align_items="center",
            ),
            rx.divider(orientation="vertical", height="28px", margin_x="3"),
            rx.hstack(
                rx.icon("users", size=18, color=rx.color("mauve", 10)),
                rx.text("Participants:", size="2", color=rx.color("mauve", 10)),
                rx.foreach(
                    ChatState.chat_participants, render_participant
                ),
                spacing="2",
                align_items="center",
                flex_wrap="wrap",
            ),
            width="100%",
            justify_content="space-between",
            padding_y="2",
            padding_x="4",
            background_color=rx.color("mauve", 2),
            border_radius="md",
            border=f"1px solid {rx.color('mauve', 4)}",
            box_shadow="sm",
            gap="2",
            align_items="center",  # <--- Add this
        ),
        width="100%",
        padding_x="2",
        padding_y="2",
        spacing="3",
        gap="2",
        align_items="center",  # <--- Add this to vstack
    )


def chat() -> rx.Component:
    """The main chat component."""
    return rx.box(
        rx.vstack(
            chat_stats_bar(), 
            chat_messages(),
            justify_content="center",
            on_mount=ChatState.scroll_to_bottom,  # Add scroll on mount
        ),  # Centered stats bar
        flex="1",
        min_height="0",
        width="100%",
        id="chat-container",
        margin = "2em",
        padding_x="4px",
        align_self="center",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.box(
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
                        rx.hstack(
                            rx.button(
                                rx.cond(
                                    ChatState.is_processing,
                                    loading_icon(height="1em"),
                                    rx.text(ChatState.submit_button_text),
                                ),
                                type="submit",
                                color_scheme=ChatState.submit_button_color,
                                is_disabled=~ChatState.can_send_message,
                            ),
                            transcribe_button(),
                            spacing="2",
                        ),
                        align_items="center",
                    ),
                    is_disabled=~ChatState.can_send_message,
                ),
                on_submit=ChatState.handle_message_submit,
                reset_on_submit=False,
            ),
            rx.input(
                value=ChatState.scroll_flag,
                display="none",
                on_change=ChatState.scroll_to_bottom,
            ),
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        z_index="10",
        padding_y="2em",
        padding_x="2em",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
    )
