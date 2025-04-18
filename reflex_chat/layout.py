from reflex_chat.components.navbar import navbar
from reflex_chat.components.sidebar import sidebar
import reflex as rx

def layout(*children):
    return rx.box(
        rx.vstack(
            navbar(),
            rx.hstack(
                sidebar(),
                rx.box(*children, flex="1", height="100%"),  # Main content fills space
                height="100%",
                width="100%",
                spacing="0",
            ),
            flex="1",  # Make vstack fill the parent box
        ),
        width="100vw",
        height="100vh",  # Fill viewport
        spacing="0",
    )