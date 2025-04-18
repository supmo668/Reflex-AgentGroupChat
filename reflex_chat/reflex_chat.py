"""The main Chat app."""

import reflex as rx
# import to trigger config code
import reflex_chat.config

from reflex_chat.components import chat, new_chat_modal
from reflex_chat.layout import layout
from reflex_chat.states.chat_state import ChatState


@rx.page(on_load=ChatState.check_and_open_modal)
def index() -> rx.Component:
    """The main app."""
    return rx.box(
        layout(
            chat.chat(),
            chat.action_bar()
        ),
        background_color=rx.color("mauve", 1),
        color=rx.color("mauve", 12),
        min_height="100vh",
        align_items="stretch",
        spacing="0",
    )


# Add state and page to the app.
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="violet",
    ),
)
app.add_page(index)
