"""The main Chat app."""

import reflex as rx
import reflex_chakra as rc

from reflex_chat.components import chat, chat_list
from reflex_chat.states.chat_state import ChatState

@rx.page(on_load=ChatState.check_and_open_modal)
def index() -> rx.Component:
    """The main app."""
    return rx.vstack(
        chat_list.chat_list(),
        chat.chat(),
        chat.action_bar(),
        # Include the modal that will be controlled by show_modal state
        # We're using the unpacked form to avoid passing None to dialog.trigger
        chat_list.modal(),
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
