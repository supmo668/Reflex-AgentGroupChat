import reflex as rx
from reflex_chat.states.chat_state import ChatState

def modal(trigger=None) -> rx.Component:
    """A modal to create a new chat."""
    dialog_content = [
        rx.dialog.content(
            rx.dialog.title(
                "Create New Chat",
                font_size="2em",
                font_weight="bold",
                color=rx.color("violet", 10),
                margin_bottom="8px",
            ),
            rx.dialog.description(
                rx.text(
                    "Give your chat a descriptive and memorable title to easily find it later.",
                    font_size="1.1em",
                    color=rx.color("mauve", 11),
                    padding_y="2",
                    margin_bottom="12px",
                    text_align="center",
                ),
                as_="div",
            ),
            rx.vstack(
                rx.input(
                    placeholder="e.g. Project Planning, AI Q&A, Brainstorming...",
                    on_blur=ChatState.set_chat_title,
                    value=ChatState.new_chat_name,
                    padding_y="4",
                    background_color=rx.color("mauve", 1),
                    border_radius="md",
                    font_size="1em",
                    box_shadow="sm",
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ChatState.close_modal,
                    ),
                    rx.button(
                        "Create",
                        on_click=ChatState.create_chat,
                        color_scheme="violet",
                        font_weight="bold",
                        box_shadow="sm",
                    ),
                    justify_content="end",
                    width="100%",
                    spacing="2",
                ),
                width="100%",
                padding_top="6",
                spacing="4",
            ),
            background_color=rx.color("mauve", 2),
            border_radius="lg",
            box_shadow="lg",
            padding="2em",
            max_width="400px",
        )
    ]
    if trigger is not None:
        dialog_content.insert(0, rx.dialog.trigger(trigger))
    return rx.dialog.root(
        *dialog_content,
        open=ChatState.show_modal,
    )