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
    def __init__(self, client):
        self.client = client
        self.stream = None
        self.running = False

    def _callback(self, indata, frames, t, status):
        print("[StreamingAudioInput._callback] Called with {} frames".format(frames))
        chunk = indata.astype(np.int16).tobytes()
        if hasattr(self.client, 'is_connected') and self.client.is_connected:
            print("[StreamingAudioInput._callback] Appending {} bytes to buffer".format(len(chunk)))
            self.client.append_audio_buffer(chunk)
        else:
            print("[StreamingAudioInput._callback] Client not connected, skipping append")

    def start(self):
        print("[StreamingAudioInput.start] Starting audio stream")
        if self.stream is not None:
            print("[StreamingAudioInput.start] Stream already started")
            return
        self.stream = sd.InputStream(
            samplerate=48000,
            channels=1,
            dtype='int16',
            callback=self._callback,
            blocksize=1024
        )
        self.stream.start()
        self.running = True
        print("[StreamingAudioInput.start] Stream started")

    def stop(self):
        print("[StreamingAudioInput.stop] Stopping audio stream")
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.running = False
            print("[StreamingAudioInput.stop] Stream stopped, calling _send()")
            self._send()
        else:
            print("[StreamingAudioInput.stop] Stream already stopped")

    def _send(self):
        print("[StreamingAudioInput._send] Committing buffer and requesting response")
        self.client.commit_audio_buffer()
        self.client.create_response()

class BufferedAudioInput:
    """
    Records audio to a buffer and sends the full stream to OpenAI after completion.
    On stop(), sends the full audio buffer as a single message and clears the buffer.
    Usage:
        b = BufferedAudioInput(client)
        b.start()
        # Recording happens automatically via callback
        ...
        b.stop()  # Sends the full audio buffer
    """
    def __init__(self, client):
        self.client = client
        self.stream = None
        self.frames = []

    def _callback(self, indata, frames, t, status):
        print(f"[BufferedAudioInput._callback] Called with {frames} frames")
        self.frames.append(indata.copy())

    def start(self):
        print("[BufferedAudioInput.start] Starting audio stream")
        if self.stream is not None:
            print("[BufferedAudioInput.start] Stream already started")
            return
        self.frames = []
        self.stream = sd.InputStream(
            samplerate=48000,
            channels=1,
            dtype='int16',
            blocksize=1024,
            callback=self._callback
        )
        self.stream.start()
        print("[BufferedAudioInput.start] Stream started")

    def stop(self):
        print("[BufferedAudioInput.stop] Stopping audio stream")
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("[BufferedAudioInput.stop] Stream stopped, calling _send()")
            self._send()
        else:
            print("[BufferedAudioInput.stop] Stream already stopped")

    @staticmethod
    def save_audio(audio, samplerate=48000):
        import tempfile
        from scipy.io.wavfile import write
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_path = f.name
            write(wav_path, samplerate, audio)
        print(f"[BufferedAudioInput.save_audio] Saved audio to {wav_path}")
        return wav_path

    @staticmethod
    def play_audio(wav_path):
        import subprocess
        print(f"[BufferedAudioInput.play_audio] Playing audio from {wav_path}")
        try:
            proc = subprocess.Popen([
                "aplay", "-D", "plughw:0,0", wav_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.wait()
        except Exception as e:
            print(f"[BufferedAudioInput.play_audio] Error playing back audio: {e}")

    def _send(self):
        print("[BufferedAudioInput._send] Sending full audio buffer to OpenAI")
        if self.frames:
            audio = np.concatenate(self.frames, axis=0).flatten()
            print(f"[BufferedAudioInput._send] Sending {audio.nbytes} bytes")
            wav_path = self.save_audio(audio, 48000)
            self.play_audio(wav_path)
            self.client.send_full_audio(audio.tobytes())
            self.client.create_response()
            self.frames = []
        else:
            print("[BufferedAudioInput._send] No frames to send")