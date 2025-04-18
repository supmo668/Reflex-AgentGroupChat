import reflex as rx
from reflex_chat.components.audio_recorder import audio_recorder
from reflex_chat.states.transcription import TranscriptionState


def transcribe_button() -> rx.Component:
    """Voice transcription button component.
    
    Returns:
        A component with the audio recorder and transcription status.
    """
    return rx.box(
        audio_recorder(),
        rx.cond(
            TranscriptionState.transcript != "",
            rx.tooltip(
                rx.icon("check", color="green", size=16),
                content=f"Transcribed: {TranscriptionState.transcript}",
            ),
            rx.text(""),
        ),
        margin_left="2",
    )
