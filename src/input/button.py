# src/input/button.py
import time
from gpiozero import Button


class AirBuddyButton:
    def __init__(self, gpio_pin=17, double_click_ms=350):
        self.button = Button(gpio_pin, pull_up=True, bounce_time=0.05)

        self.double_click_s = double_click_ms / 1000.0
        self._last_press_time = 0
        self._click_count = 0

    def wait_for_action(self):
        """
        Blocking call.
        Returns:
            "single" or "double"
        """
        self.button.wait_for_press()
        now = time.monotonic()

        if now - self._last_press_time <= self.double_click_s:
            self._click_count += 1
        else:
            self._click_count = 1

        self._last_press_time = now

        # wait briefly to see if a second click arrives
        time.sleep(self.double_click_s)

        if self._click_count >= 2:
            self._click_count = 0
            return "double"

        self._click_count = 0
        return "single"
