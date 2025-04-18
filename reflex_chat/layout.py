from reflex_chat.components.navbar import navbar, sidebar
import reflex as rx

def layout(*children):
    return rx.box(
        rx.vstack(
            navbar(),
            rx.hstack(
                sidebar(),
                rx.box(*children),
            ),
        ),
        width="100vw",
        height="100vh",
        spacing="0",
    )