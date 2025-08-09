import sounddevice as sd
import numpy as np
import time

class StreamingAudioInput:
    """
    Streams audio chunks to OpenAI in real time using client.append_audio_buffer().
    On stop(), commits the buffer and requests a response.
    Usage:
        s = StreamingAudioInput(client)
        s.start()
        ...
        s.stop()  # Commits and requests response
    """
    def __init__(self, client, samplerate=48000, blocksize=1024):
        self.client = client
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.stream = None
        self.running = False

    def _callback(self, indata, frames, t, status):
        chunk = indata.astype(np.int16).tobytes()
        if hasattr(self.client, 'is_connected') and self.client.is_connected:
            self.client.append_audio_buffer(chunk)

    def start(self):
        """Start streaming audio to OpenAI."""
        if self.stream is not None:
            return
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype='int16',
            callback=self._callback,
            blocksize=self.blocksize
        )
        self.stream.start()
        self.running = True

    def stop(self):
        """Stop streaming audio, commit buffer, and request response."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.running = False
            self._send()

    def _send(self):
        """Commit the audio buffer and request a response."""
        self.client.commit_audio_buffer()
        self.client.create_response()

class BufferedAudioInput:
    """
    Records audio to a buffer and sends the full stream to OpenAI after completion.
    On stop(), sends the full audio buffer as a single message.
    Usage:
        b = BufferedAudioInput(client)
        b.start()
        ...
        b.stop()  # Sends the full audio buffer
    """
    def __init__(self, client, samplerate=48000, blocksize=1024):
        self.client = client
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.stream = None
        self.frames = []
        self.running = False

    def start(self):
        """Start recording audio to buffer."""
        if self.stream is not None:
            return
        self.frames = []
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype='int16',
            blocksize=self.blocksize
        )
        self.stream.start()
        self.running = True

    def stop(self):
        """Stop recording audio and send the full buffer as a message."""
        if self.stream is not None:
            while True:
                frame, _ = self.stream.read(self.blocksize)
                self.frames.append(frame)
                if not self.running:
                    break
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.running = False
            self._send()

    def _send(self):
        """Send the full audio buffer to OpenAI as a single message."""
        if self.frames:
            audio = np.concatenate(self.frames, axis=0)
            self.client.send_full_audio(audio.tobytes())