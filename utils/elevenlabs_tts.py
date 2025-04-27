import os
# from elevenlabs import APIError
import uuid
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def text_to_speech_file(text: str, filename: str) -> str:
    """
    Converts text to speech and saves it to 'voice_outputs' folder.
    If API fails, prints an error and returns an empty string.
    """
    try:
        response = client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_turbo_v2",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        output_dir = "voice_outputs"
        os.makedirs(output_dir, exist_ok=True)
        save_file_path = os.path.join(output_dir, filename)

        with open(save_file_path, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)

        print(f"✅ Voice narration saved at {save_file_path}")
        return save_file_path


    except Exception as e:
        print("", str(e))
        return ""