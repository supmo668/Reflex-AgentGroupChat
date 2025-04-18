from urllib.request import urlopen
import reflex as rx
from openai import AsyncOpenAI
import logging

from reflex_audio_capture import get_codec, strip_codec_part
from reflex_chat.states.chat_state import ChatState

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI()


class TranscriptionState(rx.State):
    """State for handling audio transcription."""
    
    has_error: bool = False
    processing: bool = False
    transcript: str = ""
    timeslice: int = 5000  # 5 seconds
    device_id: str = ""
    use_mp3: bool = True
    
    async def on_data_available(self, chunk: str):
        """Process audio data and transcribe it.
        
        Args:
            chunk: Audio data chunk in base64 format.
        """
        mime_type, _, codec = get_codec(chunk).partition(";")
        audio_type = mime_type.partition("/")[2]
        if audio_type == "mpeg":
            audio_type = "mp3"
        
        logger.debug(f"Processing audio chunk: {len(chunk)} bytes, {mime_type}, {codec}, {audio_type}")
        
        with urlopen(strip_codec_part(chunk)) as audio_data:
            try:
                self.processing = True
                yield
                
                # Transcribe using OpenAI Whisper
                transcription = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("temp." + audio_type, audio_data.read(), mime_type),
                )
                
                # Update transcript
                self.transcript = transcription.text
                logger.debug(f"Transcription: {self.transcript}")
                
                # Set the transcribed text as the current message
                await ChatState.set_user_message(self.transcript)
                
            except Exception as e:
                self.has_error = True
                logger.error(f"Transcription error: {str(e)}")
                yield rx.window_alert(f"Error transcribing audio: {str(e)}")
            finally:
                self.processing = False
    
    def on_error(self, err):
        """Handle errors from the audio recorder.
        
        Args:
            err: Error message.
        """
        logger.error(f"Audio recorder error: {err}")
        self.has_error = True
