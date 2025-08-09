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
            samplerate=self.samplerate,
            channels=1,
            dtype='int16',
            callback=self._callback,
            blocksize=self.blocksize
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
        print("[BufferedAudioInput.start] Starting audio stream")
        if self.stream is not None:
            print("[BufferedAudioInput.start] Stream already started")
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
        print("[BufferedAudioInput.start] Stream started")

    def stop(self):
        print("[BufferedAudioInput.stop] Stopping audio stream")
        if self.stream is not None:
            while True:
                frame, _ = self.stream.read(self.blocksize)
                print(f"[BufferedAudioInput.stop] Read {len(frame)} samples")
                self.frames.append(frame)
                if not self.running:
                    break
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.running = False
            print("[BufferedAudioInput.stop] Stream stopped, calling _send()")
            self._send()
        else:
            print("[BufferedAudioInput.stop] Stream already stopped")

    def _send(self):
        print("[BufferedAudioInput._send] Sending full audio buffer to OpenAI")
        if self.frames:
            audio = np.concatenate(self.frames, axis=0)
            print(f"[BufferedAudioInput._send] Sending {audio.nbytes} bytes")
            self.client.send_full_audio(audio.tobytes())
            self.client.create_response()
        else:
            print("[BufferedAudioInput._send] No frames to send")