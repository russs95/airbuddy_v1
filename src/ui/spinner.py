import time


class Spinner:
    """
    Center-to-full-width breathing bar spinner.

    Visual behavior:
    - Horizontal expansion/contraction is the primary motion
    - A subtle "vertical pulse" (thickness flag) occurs near peak width
    - Fixed total width ensures perfect centering with no jitter
    """

    # ======================================================
    # 🔧 TUNABLE ANIMATION PARAMETERS
    # ======================================================

    TOTAL_CHARS = 16        # Total character width of the spinner line
    # (Should match OLED width & font size)

    MIN_BAR_CHARS = 2       # Narrowest bar width (calm / contracted state)
    MAX_BAR_CHARS = 16      # Widest bar width (peak / inhale state)

    BAR_STEP = 2            # Number of characters added per frame
    # Smaller = smoother, slower breathing
    # Larger = punchier, more mechanical

    FRAME_INTERVAL = 0.05   # Seconds between frames (animation speed)
    # Lower = faster, higher = calmer

    PEAK_THICKNESS_MARGIN = 3
    # How close to max width the bar must be
    # before triggering the "thick" (vertical pulse)

    # ======================================================

    def __init__(self, oled):
        self.oled = oled

        # Precompute animation frames once (important for smooth rendering)
        self.frames = self._build_frames()

    def _build_frames(self):
        """
        Generate all animation frames from narrow → wide → narrow.

        Each frame contains:
        - text  : fixed-width string for centering stability
        - thick : boolean flag for subtle vertical emphasis
        """

        frames = []

        # Build width progression for inhale (expand)
        widths_up = list(
            range(self.MIN_BAR_CHARS, self.MAX_BAR_CHARS + 1, self.BAR_STEP)
        )

        # Build width regression for exhale (contract)
        widths_down = list(
            range(self.MAX_BAR_CHARS - self.BAR_STEP,
                  self.MIN_BAR_CHARS - 1,
                  -self.BAR_STEP)
        )

        # Full breathing cycle
        widths = widths_up + widths_down

        for w in widths:
            # Center the bar horizontally
            pad = (self.TOTAL_CHARS - w) // 2

            # Construct fixed-width bar
            text = (" " * pad) + ("█" * w) + (" " * pad)

            # Ensure constant string length to avoid OLED jitter
            text = text.ljust(self.TOTAL_CHARS)

            # Trigger vertical pulse only near peak expansion
            thick = (w >= self.MAX_BAR_CHARS - self.PEAK_THICKNESS_MARGIN)

            frames.append({
                "text": text,
                "thick": thick
            })

        return frames

    def spin(self, duration=6):
        """
        Play the spinner animation for a fixed duration.

        Args:
            duration (float): total runtime in seconds
        """

        end_time = time.time() + duration
        frame_index = 0
        total_frames = len(self.frames)

        while time.time() < end_time:
            self.oled.show_spinner_frame(self.frames[frame_index])

            # Advance frame index with wraparound
            frame_index = (frame_index + 1) % total_frames

            time.sleep(self.FRAME_INTERVAL)
