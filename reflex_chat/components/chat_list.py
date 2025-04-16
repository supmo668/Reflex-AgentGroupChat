import reflex as rx
from reflex_chat.states.chat_state import ChatState, ChatSession
from .new_chat_modal import modal

def sidebar_chat(chat_session: ChatSession) -> rx.Component:
    """A sidebar chat item.

    Args:
        chat_session: The chat session to display.
    """
    return rx.drawer.close(
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon("message-circle", size=16),
                    chat_session.name,
                    width="100%",
                    spacing="2",
                ),
                on_click=lambda: ChatState.switch_chat(chat_session.id),
                width="80%",
                variant="surface",
            ),
            rx.button(
                rx.icon(
                    tag="trash",
                    on_click=lambda: ChatState.delete_chat(chat_session.id),
                    stroke_width=1,
                ),
                width="20%",
                variant="surface",
                color_scheme="red",
            ),
            width="100%",
        )
    )


def chat_list() -> rx.Component:
    """The chat list component."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.avatar(fallback="RC", variant="solid"),
                rx.heading("Reflex Chat"),
                rx.desktop_only(
                    rx.badge(
                        ChatState.current_session.name,
                        rx.tooltip(
                            rx.icon("info", size=14),
                            content="The current selected chat."
                        ),
                        variant="soft"
                    )
                ),
                align_items="center",
            ),
            rx.hstack(
                modal(rx.button("+ New chat", on_click=ChatState.open_modal)),
                rx.drawer.root(
                    rx.drawer.trigger(
                        rx.button(
                            rx.icon(
                                tag="messages-square",
                                color=rx.color("mauve", 12),
                            ),
                            background_color=rx.color("mauve", 6),
                        )
                    ),
                    rx.drawer.overlay(),
                    rx.drawer.portal(
                        rx.drawer.content(
                            rx.vstack(
                                rx.heading("Chats", color=rx.color("mauve", 11)),
                                rx.divider(),
                                rx.foreach(
                                    ChatState.session_list,
                                    sidebar_chat
                                ),
                                align_items="stretch",
                                width="100%",
                            ),
                            top="auto",
                            right="auto",
                            height="100%",
                            width="20em",
                            padding="2em",
                            background_color=rx.color("mauve", 2),
                            outline="none",
                        )
                    ),
                    direction="left",
                ),
                rx.desktop_only(
                    rx.button(
                        rx.icon(
                            tag="sliders-horizontal",
                            color=rx.color("mauve", 12),
                        ),
                        background_color=rx.color("mauve", 6),
                    )
                ),
                align_items="center",
            ),
            justify_content="space-between",
            align_items="center",
        ),
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
