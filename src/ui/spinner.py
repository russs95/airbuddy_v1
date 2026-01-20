import time

class Spinner:
    """
    OLED progress-bar spinner.
    """
    def __init__(self, oled, width=10, interval=0.12):
        self.oled = oled
        self.width = width
        self.interval = interval

    def spin(self, duration=3, label="Reading..."):
        end = time.time() + duration
        direction = 1
        pos = 0

        while time.time() < end:
            bar = "█" * pos + "░" * (self.width - pos)
            self.oled.text([
                label,
                f"[{bar}]"
            ])

            pos += direction
            if pos >= self.width:
                pos = self.width
                direction = -1
            elif pos <= 0:
                pos = 0
                direction = 1

            time.sleep(self.interval)
