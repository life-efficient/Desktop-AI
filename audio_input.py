import sounddevice as sd
import numpy as np
import time

class StreamingAudioInput:
    """
    Streams audio chunks to OpenAI in real time using client.append_audio_buffer().
    Usage:
        s = StreamingAudioInput(client)
        s.start()
        ...
        s.stop()
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
        """Stop streaming audio."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.running = False
    def send(self):
        """No-op for streaming input (audio is sent in real time)."""
        pass

class BufferedAudioInput:
    """
    Records audio to a buffer and sends the full stream to OpenAI after completion.
    Usage:
        b = BufferedAudioInput(client)
        b.start()
        ...
        b.stop()
        b.send()
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
        """Stop recording audio."""
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
    def send(self):
        """Send the full audio buffer to OpenAI using client.send_audio_message()."""
        if self.frames:
            audio = np.concatenate(self.frames, axis=0)
            self.client.send_audio_message(audio.tobytes())