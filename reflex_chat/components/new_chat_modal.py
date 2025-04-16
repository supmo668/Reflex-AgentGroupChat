import reflex as rx
from reflex_chat.states.chat_state import ChatState

def modal(trigger=None) -> rx.Component:
    """A modal to create a new chat.
    
    Args:
        trigger: Optional trigger component. If not provided, the modal will be controlled by show_modal state.
    """
    # Create dialog with or without trigger
    dialog_content = [
        rx.dialog.content(
            rx.dialog.title("Create New Chat"),
            rx.dialog.description(
                "Enter a title for your new chat."
            ),
            rx.vstack(
                rx.input(
                    placeholder="Chat title",
                    on_change=ChatState.set_chat_title,
                    value=ChatState.new_chat_name,
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
                    ),
                    justify_content="end",
                    width="100%",
                ),
                width="100%",
                padding_top="4",
                spacing="3",
            ),
        )
    ]
    
    # Add trigger if provided
    if trigger is not None:
        dialog_content.insert(0, rx.dialog.trigger(trigger))
    
    return rx.dialog.root(
        *dialog_content,

        open=ChatState.show_modal,
    )
