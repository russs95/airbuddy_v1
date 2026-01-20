import time


class Spinner:
    """
    Center-to-full-width breathing bar.
    Horizontal expansion is the main motion.
    Vertical pulse is subtle via a thickness effect at peak.
    """

    def __init__(self, oled, interval=0.12):
        self.oled = oled
        self.interval = interval

        # Build frames from narrow to wide to narrow.
        # Use a fixed total width so centering is stable.
        self.total_chars = 16  # fits well at font size ~22 on 128px wide OLED
        self.min_bar = 2
        self.max_bar = 16

        widths_up = list(range(self.min_bar, self.max_bar + 1, 2))
        widths_down = list(range(self.max_bar - 2, self.min_bar - 1, -2))
        widths = widths_up + widths_down

        frames = []
        for w in widths:
            pad = (self.total_chars - w) // 2
            text = (" " * pad) + ("█" * w) + (" " * pad)
            # ensure constant length to avoid jitter
            text = text.ljust(self.total_chars)

            # subtle vertical pulse only near the widest point
            thick = (w >= self.max_bar - 2)
            frames.append({"text": text, "thick": thick})

        self.frames = frames

    def spin(self, duration=6):
        end_time = time.time() + duration
        i = 0
        n = len(self.frames)

        while time.time() < end_time:
            self.oled.show_spinner_frame(self.frames[i])
            i = (i + 1) % n
            time.sleep(self.interval)
