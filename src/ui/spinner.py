import time


class Spinner:
    """
    Bigger, centered breathing-bar spinner for SSD1306.
    Uses OLED.show_spinner_frame() for reduced flicker.
    """

    def __init__(self, oled, interval=0.18):
        self.oled = oled
        self.interval = interval

        # Wider frames so it looks substantial in large font
        self.frames = [
            "▁▁▁▁▁▁▁▁▁",
            "▃▃▃▃▃▃▃▃▃",
            "▄▄▄▄▄▄▄▄▄",
            "▆▆▆▆▆▆▆▆▆",
            "█████████",
            "▆▆▆▆▆▆▆▆▆",
            "▄▄▄▄▄▄▄▄▄",
            "▃▃▃▃▃▃▃▃▃",
        ]

    def spin(self, duration=6, label="Sampling air"):
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            self.oled.show_spinner_frame(label, self.frames[i])
            i = (i + 1) % len(self.frames)
            time.sleep(self.interval)
