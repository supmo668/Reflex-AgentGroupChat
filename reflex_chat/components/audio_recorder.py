import reflex as rx
from reflex_audio_capture import AudioRecorderPolyfill
from reflex_chat.states.transcription import TranscriptionState

REF = "chat_audio"

# Create the audio recorder polyfill
capture = AudioRecorderPolyfill.create(
    id=REF,
    on_data_available=TranscriptionState.on_data_available,
    on_error=TranscriptionState.on_error,
    timeslice=TranscriptionState.timeslice,
    device_id=TranscriptionState.device_id,
    use_mp3=TranscriptionState.use_mp3,
)


def audio_recorder() -> rx.Component:
    """Audio recorder component for voice input."""
    return rx.hstack(
        capture,
        rx.cond(
            capture.is_recording,
            rx.button(
                rx.icon("square", size=16),  # Use "square" as stop icon
                on_click=capture.stop(),
                color_scheme="red",
                variant="outline",
            ),
            rx.button(
                rx.icon("mic", size=16),
                on_click=capture.start(),
                color_scheme="green",
                variant="outline",
            ),
        ),
        rx.cond(
            TranscriptionState.processing,
            rx.spinner(size="1", color="blue"),
            rx.text(""),
        ),
        spacing="1",
    )