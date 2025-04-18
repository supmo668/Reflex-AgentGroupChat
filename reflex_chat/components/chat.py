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
    bar_height = "28px"
    return rx.box(
        rx.cond(
            ChatState.current_session,
            rx.cond(
                ChatState.has_messages,
                rx.foreach(ChatState.messages, message),
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
        rx.el.div(id=BOTTOM_ELEMENT_ID, style={"height": "1px"}),
        overflow_y="auto",
        flex="1",
        min_height="0",
        width="100%",
        padding_x="4px",
        padding_top=bar_height,
        id="chat-messages-area",
        style={
            "scrollbarWidth": "none",         # Firefox
            "msOverflowStyle": "none",        # IE/Edge
        },
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
            padding="2",
            align_items="center",
            width="100%",
            justify_content="flex-start",
        ),
        rx.hstack(
            rx.icon("message_circle", size=18, color=rx.color("violet", 9)),
            rx.text(f"Messages: {ChatState.message_count}", size="2", color=rx.color("mauve", 10)),
            rx.divider(orientation="vertical", height="28px", margin_x="3"),
            rx.icon("users", size=18, color=rx.color("mauve", 10)),
            rx.text("Participants:", size="2", color=rx.color("mauve", 10)),
            rx.foreach(ChatState.chat_participants, render_participant),
            spacing="2",
            padding="2",
            align_items="center",
            width="100%",
            justify_content="flex-start",
        ),
        width="100%",
        background_color=rx.color("mauve", 2),
        box_shadow="sm",
        border_bottom=f"2px solid {rx.color('mauve', 4)}",
    )

def action_bar() -> rx.Component:
    return rx.box(
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
        width="100%",
        z_index="10",
        background_color=rx.color("mauve", 3),
        border_top=f"4px solid {rx.color('mauve', 6)}",
        box_shadow="md",
        padding_y="1em",
        padding_x="2em",
    )

def chat() -> rx.Component:
    return rx.box(
        chat_stats_bar(),
        chat_messages(),  # This is the only scrollable area
        action_bar(),
        display="flex",
        flex_direction="column",
        height="100%",
        width="100%",
        position="relative",
        id="chat-container",
        background_color=rx.color("mauve", 1),
    )