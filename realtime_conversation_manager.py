import asyncio
import json
import websockets
import os
from dotenv import load_dotenv
from logging_util import get_logger

load_dotenv()
logger = get_logger(__name__)

OPENAI_REALTIME_WS_URL = "wss://api.openai.com/v1/realtime"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

class RealtimeConversationManager:
    def __init__(self, model="gpt-4o", tools=None):
        self.model = model
        self.tools = tools or []
        self.session_id = None
        self.ws = None
        self.history = []  # Store conversation history

    async def connect(self):
        self.ws = await websockets.connect(
            OPENAI_REALTIME_WS_URL,
            extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
        )
        logger.info("Connected to OpenAI Realtime API.")

    async def send_user_audio(self, audio_bytes, mime_type="audio/wav"):
        # For voice, send audio as a binary message with metadata
        payload = {
            "model": self.model,
            "messages": self.history,
            "tools": self.tools,
            "input_type": "audio",
            "audio_mime_type": mime_type,
        }
        await self.ws.send(json.dumps(payload))
        await self.ws.send(audio_bytes)  # Send audio as binary frame
        logger.info("Sent user audio to OpenAI.")

    async def send_user_text(self, text):
        # For debugging or fallback, send text as a message
        user_msg = {"role": "user", "content": text}
        self.history.append(user_msg)
        payload = {
            "model": self.model,
            "messages": self.history,
            "tools": self.tools,
        }
        await self.ws.send(json.dumps(payload))
        logger.info("Sent user text to OpenAI.")

    async def receive_stream(self):
        async for msg in self.ws:
            # OpenAI may send text, tool calls, or TTS audio chunks
            if isinstance(msg, bytes):
                # Handle audio chunk (TTS response)
                yield {"type": "audio", "data": msg}
            else:
                data = json.loads(msg)
                logger.info(f"Received: {data}")
                yield data

    async def close(self):
        await self.ws.close()
        logger.info("Closed WebSocket connection.") 