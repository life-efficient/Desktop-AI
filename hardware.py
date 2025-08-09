import RPi.GPIO as GPIO
import time

# Pin assignments (BCM numbering)
BUTTON_PIN = 17
LED_PIN = 27
SPEAKER_SHUTDOWN_PIN = 22

class Hardware:
    """
    Hardware abstraction for Raspberry Pi GPIO: LED, button, and speaker control.
    Call cleanup() when done to safely release GPIO resources.
    """
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.setup(SPEAKER_SHUTDOWN_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)
        self._cleaned = False

    def led_on(self):
        """Turn the LED on (full brightness)."""
        GPIO.output(LED_PIN, GPIO.HIGH)

    def led_off(self):
        """Turn the LED off."""
        GPIO.output(LED_PIN, GPIO.LOW)

    def enable_speaker(self):
        """Enable the speaker amplifier."""
        GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.HIGH)

    def disable_speaker(self):
        """Disable the speaker amplifier."""
        GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)

    def button_pressed(self):
        """Return True if the button is currently pressed (active low)."""
        return GPIO.input(BUTTON_PIN) == GPIO.LOW

    def cleanup(self):
        """Clean up all GPIO resources (turn off LED, disable speaker, release pins)."""
        if not self._cleaned:
            self.led_off()
            self.disable_speaker()
            GPIO.cleanup()
            self._cleaned = True