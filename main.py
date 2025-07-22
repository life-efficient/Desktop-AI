import sounddevice as sd
from scipy.io.wavfile import write, read
import RPi.GPIO as GPIO
import numpy as np
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import threading
import math
import logging
from conversation_manager import ConversationManager

# Set up logging
LOGFILE = "/home/pi/desktop-ai-logs/main.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGFILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not client.api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# GPIO Setup
BUTTON_PIN = 17
LED_PIN = 27
SPEAKER_SHUTDOWN_PIN = 22  # GPIO for speaker amplifier shutdown
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(SPEAKER_SHUTDOWN_PIN, GPIO.OUT)
GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)  # Start with speaker disabled

class LEDPatternController:
    """Controls LED patterns using PWM"""
    
    PATTERNS = {
        "solid": "Steady brightness",
        "blink": "On/off blinking",
        "pulse": "Smooth breathing effect"
    }
    
    def __init__(self, pin, pwm_freq=100):
        """Initialize LED controller
        
        Args:
            pin: GPIO pin number
            pwm_freq: PWM frequency in Hz
        """
        self.pin = pin
        self.pwm_freq = pwm_freq
        self.pwm = None
        self.pattern = "solid"
        self.running = False
        self.thread = None
    
    def _setup_pwm(self):
        """Initialize PWM if not already set up"""
        if self.pwm is None:
            self.pwm = GPIO.PWM(self.pin, self.pwm_freq)
            self.pwm.start(0)
    
    def _pattern_loop(self):
        """Main pattern control loop"""
        self._setup_pwm()
        
        try:
            while self.running:
                if self.pattern == "solid":
                    self.pwm.ChangeDutyCycle(100)
                    time.sleep(0.1)
                
                elif self.pattern == "blink":
                    self.pwm.ChangeDutyCycle(100)
                    time.sleep(0.5)
                    if not self.running:
                        break
                    self.pwm.ChangeDutyCycle(0)
                    time.sleep(0.5)
                
                elif self.pattern == "pulse":
                    # Fade in
                    for dc in range(0, 101, 2):
                        if not self.running:
                            break
                        self.pwm.ChangeDutyCycle(dc)
                        time.sleep(0.01)
                    # Fade out
                    for dc in range(100, -1, -2):
                        if not self.running:
                            break
                        self.pwm.ChangeDutyCycle(dc)
                        time.sleep(0.01)
        finally:
            self.pwm.ChangeDutyCycle(0)
    
    def start(self, pattern=None):
        """Start LED pattern
        
        Args:
            pattern: Optional pattern to use (solid, blink, or pulse)
        """
        if pattern is not None:
            if pattern not in self.PATTERNS:
                raise ValueError(f"Invalid pattern. Choose from: {', '.join(self.PATTERNS.keys())}")
            self.pattern = pattern
        
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._pattern_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """Stop LED pattern"""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        GPIO.output(self.pin, GPIO.LOW)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        if self.pwm is not None:
            self.pwm.stop()
            self.pwm = None
    
    @property
    def available_patterns(self):
        """Get list of available patterns with descriptions"""
        return self.PATTERNS

def enable_speaker():
    """Enable the speaker amplifier."""
    logger.info("Enabling speaker.")
    GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.HIGH)

def disable_speaker():
    """Disable the speaker amplifier."""
    logger.info("Disabling speaker.")
    GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)

RECORDING_FILE = Path("/tmp/recording.wav")
RESPONSE_AUDIO_FILE = Path("/tmp/response.wav")
SAMPLERATE = 48000
CHANNELS = 1

def transcribe_audio(audio_file):
    """
    Transcribe the recorded audio using OpenAI's GPT-4 Transcribe model
    """
    try:
        with open(audio_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=file
            )
            return transcription.text
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return None

def generate_speech(text):
    """
    Generate speech from text using OpenAI's TTS API with streaming
    """
    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text,
            response_format="wav"
        ) as response:
            response.stream_to_file(RESPONSE_AUDIO_FILE)
        return True
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return False

def play_audio(filename):
    """
    Play audio file non-blockingly using aplay.
    Manages the global playback_process.
    """
    global playback_process
    stop_audio_playback()  # Stop any previous playback first
    try:
        enable_speaker()  # Turn speaker on
        # Use DEVNULL to hide aplay's stdout/stderr messages
        playback_process = subprocess.Popen(
            ["aplay", "-D", "plughw:0,0", str(filename)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        logger.error(f"Error starting audio playback: {e}")
        disable_speaker()  # Turn speaker off on error
        playback_process = None

def stop_audio_playback():
    """Stops the currently playing audio."""
    global playback_process
    if playback_process and playback_process.poll() is None:
        logger.info("Interrupting audio playback.")
        playback_process.terminate()
        try:
            # Wait for a moment to allow graceful termination
            playback_process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop
            playback_process.kill()
        playback_process = None
        disable_speaker()  # Turn speaker off
        return True
    return False

def cleanup(e=None):
    if e is not None:
        logger.error(f"Error: {e}")
    play_audio(Path(__file__).parent / "sounds" / "Error.wav")
    led.cleanup()  # Clean up LED resources
    stop_audio_playback() # Ensure audio is stopped
    GPIO.cleanup()
    logger.info("Exiting")

# Initialize conversation manager and LED controller
conversation = ConversationManager()
led = LEDPatternController(LED_PIN)

# Set desired pattern
LED_PATTERN = "pulse"  # Can be "solid", "blink", or "pulse"

logger.info("Waiting for button press...")
logger.info(f"Current conversation has {len(conversation.messages)} messages")
logger.info(f"LED Pattern: {LED_PATTERN}")
logger.info("Available patterns: " + ", ".join(f"{k} ({v})" for k, v in led.available_patterns.items()))

recording = []
stream = None
playback_process = None

play_audio(Path(__file__).parent / "sounds" / "Bloop.wav")

try:
    while True:
        button_is_down = GPIO.input(BUTTON_PIN) == GPIO.LOW

        if button_is_down:
            # If assistant is speaking, interrupt it
            if playback_process and playback_process.poll() is None:
                stop_audio_playback()

            # If not already recording, start a new recording
            if stream is None:
                logger.info("Button pressed – recording...")
                led.start(LED_PATTERN)
                recording = []
                stream = sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype='int16')
                stream.start()
            
            # While recording, read data from the stream
            if stream:
                frame, _ = stream.read(1024)
                recording.append(frame)
        
        else: # Button is up
            if stream is not None:
                logger.info("Button released – saving file...")
                led.stop()
                stream.stop()
                stream.close()
                stream = None

                if not recording:
                    logger.warning("No audio recorded.")
                    continue

                audio = np.concatenate(recording, axis=0)
                write(RECORDING_FILE, SAMPLERATE, audio)
                logger.info(f"Saved to {RECORDING_FILE}")
                
                # Play Drip sound after button release
                play_audio(Path(__file__).parent / "sounds" / "Drip.wav")
                
                # Transcribe the recorded audio
                logger.info("Transcribing audio...")
                transcription = transcribe_audio(RECORDING_FILE)
                if transcription:
                    logger.info(f"Transcription: {transcription}")
                    
                    # Add transcription to conversation and get response
                    conversation.add_message("user", transcription)
                    logger.info("Generating response...")
                    response = conversation.generate_response()
                    if response:
                        logger.info(f"Assistant: {response}")
                        
                        # Generate and play speech response
                        logger.info("Generating speech...")
                        if generate_speech(response):
                            logger.info("Playing response...")
                            play_audio(RESPONSE_AUDIO_FILE)
                        else:
                            logger.error("Failed to generate speech")
                    else:
                        logger.error("Failed to generate response")
                else:
                    logger.error("Transcription failed")

        # Check if playback has finished on its own
        if playback_process and playback_process.poll() is not None:
            playback_process = None
            disable_speaker()  # Turn speaker off when done

        time.sleep(0.01)

except KeyboardInterrupt:
    cleanup()

except Exception as e:
    cleanup(e)