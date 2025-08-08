import asyncio
import sounddevice as sd
import numpy as np
import io
import wave
from realtime_conversation_manager import RealtimeConversationManager
from logging_util import get_logger

logger = get_logger(__name__)

SAMPLERATE = 16000
CHANNELS = 1
AUDIO_DURATION = 5  # seconds per utterance


def record_audio(duration=AUDIO_DURATION, samplerate=SAMPLERATE, channels=CHANNELS):
    logger.info("Recording audio from microphone...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
    sd.wait()
    logger.info("Recording complete.")
    # Convert numpy array to WAV bytes
    with io.BytesIO() as buf:
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(samplerate)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()

def play_audio_bytes(audio_bytes):
    # Play WAV bytes using sounddevice
    with io.BytesIO(audio_bytes) as buf:
        with wave.open(buf, 'rb') as wf:
            samplerate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                audio = audio.reshape(-1, channels)
            sd.play(audio, samplerate=samplerate)
            sd.wait()

async def main():
    manager = RealtimeConversationManager()
    await manager.connect()
    print("Press Enter to record, or type 'exit' to quit.")
    while True:
        cmd = input("You: ").strip()
        if cmd.lower() == 'exit':
            break
        # Record audio from mic
        audio_bytes = record_audio()
        # Send to OpenAI Realtime
        await manager.send_user_audio(audio_bytes)
        print("Assistant (streaming): ", end='', flush=True)
        async for response in manager.receive_stream():
            if response["type"] == "audio":
                play_audio_bytes(response["data"])
            elif response.get("type") == "text":
                print(response.get("data", ""), end='', flush=True)
            # Optionally break on end-of-turn
        print()
    await manager.close()

if __name__ == "__main__":
    asyncio.run(main()) 