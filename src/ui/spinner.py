import time


class Spinner:
    """
    2D breathing block spinner.
    Expands/contracts horizontally and vertically using solid block glyphs.
    """

    def __init__(self, oled, interval=0.18):
        self.oled = oled
        self.interval = interval

        b = "█"
        sp = " "

        # Frames are lists of lines (vertical breathing).
        # Keep line lengths consistent so centering doesn't jitter.
        self.frames = [
            [sp*6 + b*4 + sp*6],                            # small (1 line)
            [sp*5 + b*6 + sp*5],                            # wider (1 line)
            [sp*5 + b*6 + sp*5,
             sp*5 + b*6 + sp*5],                            # taller (2 lines)
            [sp*4 + b*8 + sp*4,
             sp*4 + b*8 + sp*4],                            # bigger (2 lines)
            [sp*4 + b*8 + sp*4,
             sp*4 + b*8 + sp*4,
             sp*4 + b*8 + sp*4],                            # max breath (3 lines)
            [sp*4 + b*8 + sp*4,
             sp*4 + b*8 + sp*4],                            # contract (2 lines)
            [sp*5 + b*6 + sp*5,
             sp*5 + b*6 + sp*5],                            # contract (2 lines)
            [sp*5 + b*6 + sp*5],                            # contract (1 line)
        ]

    def spin(self, duration=6):
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            self.oled.show_spinner_frame(self.frames[i])
            i = (i + 1) % len(self.frames)
            time.sleep(self.interval)
