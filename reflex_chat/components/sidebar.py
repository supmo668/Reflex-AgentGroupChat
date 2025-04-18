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
        rx.button(
            rx.cond(
                ChatState.sidebar_open, rx.icon("chevron-left"), rx.icon("chevron-right"),
            ),
            on_click=ChatState.toggle_sidebar,
            margin_bottom="1em",
        ),
        rx.cond(
            ChatState.sidebar_open,
            rx.vstack(
                rx.heading("Chat Sessions", color=rx.color("mauve", 11)),
                rx.divider(),
                rx.button(
                    rx.hstack(
                        rx.icon("plus", size=16),
                        rx.text("New Convo", min_width="30px"),
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
                align_items="stretch",
                padding="2em",
            ),
            None
        ),
        width=rx.cond(ChatState.sidebar_open, "20em", "4em"),
        transition="width 0.2s",
        height="100%",
        background_color=rx.color("mauve", 2),
        overflow="hidden",
        align_items="start",
    )