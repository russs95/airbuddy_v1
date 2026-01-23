# src/input/button.py
import time
from gpiozero import Button


class AirBuddyButton:
    def __init__(self, gpio_pin=17, double_click_window_s=1.0):
        # pull_up=True means button to GND; pressed = LOW
        self.button = Button(gpio_pin, pull_up=True, bounce_time=0.05)
        self.double_click_window_s = float(double_click_window_s)

    def wait_for_action(self):
        """
        Blocking call.
        Returns:
            "single" or "double"
        Behavior:
            - Wait for first press
            - Then wait up to `double_click_window_s` for a second press
            - If second press happens in the window => double
            - Otherwise => single
        """
        # First press
        self.button.wait_for_press()

        # Optional: wait for release so a long hold doesn't confuse detection
        self.button.wait_for_release()

        start = time.monotonic()

        # Look for second press within the window
        while (time.monotonic() - start) < self.double_click_window_s:
            if self.button.is_pressed:
                # second press detected
                self.button.wait_for_release()
                return "double"
            time.sleep(0.01)  # light poll

        return "single"
