import reflex as rx
from reflex_chat.states.chat_state import ChatState

def navbar():
    """The navbar component."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.avatar(src="./favicon.png"),
                rx.heading("Multi-Agent Chat"),
                rx.desktop_only(
                    rx.badge(
                        rx.cond(ChatState.current_session, ChatState.current_session.name, ""),
                        rx.tooltip(rx.icon("info", size=14), content="The current selected chat."),
                        variant="soft"
                    )
                ),
                align_items="center",
            ),
            rx.hstack(
                rx.button(
                    rx.icon("plus", size=16),
                    "New Convo",
                    on_click=ChatState.open_modal,
                ),
                rx.button(
                    rx.icon(
                        tag="messages-square",
                        color=rx.color("mauve", 12),
                    ),
                    on_click=ChatState.toggle_sidebar,
                    background_color=rx.color("mauve", 6),
                ),
                align_items="center",
            ),
            justify_content="space-between",
            align_items="center",
        ),
        width="100%",  # <--- ensure full width
        backdrop_filter="auto",
        backdrop_blur="lg",
        padding="12px",
        border_bottom=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        position="sticky",
        top="0",
        z_index="100",
        align_items="center",
    )

