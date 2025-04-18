import reflex as rx
from reflex_chat.states.chat_state import ChatState

def sidebar_chat(session) -> rx.Component:
    return rx.hstack(
        rx.button(
            session.name, 
            on_click=lambda: ChatState.switch_chat(session.id), 
            width="80%", 
            variant="surface",
            color_scheme=rx.cond(
                session.id == ChatState.current_chat_id,
                "violet",
                "gray"
            ),
        ),
        rx.button(
            rx.icon(
                tag="trash",
                on_click=lambda: ChatState.delete_chat(session.id),
                stroke_width=1,
            ),
            width="20%",
            variant="surface",
            color_scheme="red",
        ),
        width="100%",
    )

def sidebar() -> rx.Component:
    return rx.box(
        rx.scroll_area(
            rx.vstack(
                rx.button(
                    rx.cond(
                        ChatState.sidebar_open, rx.icon("chevron-left"), rx.icon("chevron-right"),
                    ),
                    on_click=ChatState.toggle_sidebar,
                    margin_bottom="1em",
                ),
                rx.vstack(
                    rx.heading("Chat Sessions", color=rx.color("mauve", 11)),
                    rx.divider(),
                    rx.button(
                        rx.hstack(
                            rx.icon("plus", size=16),
                            rx.text("New Chat", min_width="30px"),
                            spacing="2",
                        ),
                        on_click=ChatState.open_modal,
                        width="100%",
                        margin_bottom="4",
                    ),
                    rx.divider(),
                    rx.foreach(
                        ChatState.session_list, sidebar_chat,
                    ),
                ),
                align_items="stretch",
                width="100%",
            ),
        ),
        width=rx.cond(ChatState.sidebar_open, "20em", "2em"),
        transition="width 0.2s",
        background_color=rx.color("mauve", 2),
        align_items="start",
    )

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
                    "New Chat",
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

