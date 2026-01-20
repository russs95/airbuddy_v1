import time


class Spinner:
    """
    2D breathing spinner (horizontal + vertical).
    Uses solid block '█' with DejaVu mono font on OLED.
    """

    def __init__(self, oled, interval=0.20, width=10):
        self.oled = oled
        self.interval = interval
        self.width = width

        # Horizontal expansion steps (how many blocks are "filled")
        # 2..width..2 creates the breathing rhythm
        up = list(range(2, self.width + 1))
        down = list(range(self.width - 1, 1, -1))
        self.h_steps = up + down

        # Vertical "thickness" steps (number of rows)
        # 1 -> 3 -> 5 -> 3 -> 1 (fits 64px height with spacing)
        self.v_steps = [1, 3, 5, 3, 1]

    def _make_frame(self, blocks, rows):
        # Centered bar string, fixed width so it doesn't jitter
        filled = "█" * blocks
        empty = " " * (self.width - blocks)
        bar = filled + empty

        # Build multi-line (vertical breathing)
        return [bar for _ in range(rows)]

    def spin(self, duration=6):
        end = time.time() + duration
        hi = 0
        vi = 0

        while time.time() < end:
            blocks = self.h_steps[hi]
            rows = self.v_steps[vi]

            frame = self._make_frame(blocks, rows)
            self.oled.show_spinner_frame(frame)

            hi = (hi + 1) % len(self.h_steps)
            vi = (vi + 1) % len(self.v_steps)

            time.sleep(self.interval)
