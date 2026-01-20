import time

class Spinner:
    def __init__(self, oled, frames=None, interval=0.12):
        self.oled = oled
        self.frames = frames or ["|", "/", "-", "\\"]
        self.interval = interval
        self.i = 0

    def _next(self) -> str:
        ch = self.frames[self.i]
        self.i = (self.i + 1) % len(self.frames)
        return ch

    def spin(self, duration=3, label="Reading..."):
        """
        Show an ASCII spinner on the OLED for `duration` seconds.
        """
        end = time.time() + duration
        while time.time() < end:
            ch = self._next()
            # Two-line display: label + spinner
            self.oled.text([label, f"[{ch}]"])
            time.sleep(self.interval)
