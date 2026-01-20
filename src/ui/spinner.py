import time


class Spinner:
    """
    Centered, font-safe breathing spinner.
    """

    def __init__(self, oled, interval=0.22):
        self.oled = oled
        self.interval = interval
        self.frames = [
            "    *    ",
            "   ***   ",
            "  *****  ",
            " ******* ",
            "  *****  ",
            "   ***   ",
        ]

    def spin(self, duration=6):
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            self.oled.show_spinner_frame(self.frames[i])
            i = (i + 1) % len(self.frames)
            time.sleep(self.interval)
