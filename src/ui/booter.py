# src/ui/booter.py
import time
from PIL import ImageFont


class Booter:
    """
    Boot screen:
      - Title: "airBuddy" in Arvo 22 (from oled.py)
      - Loading bar: DejaVuSansMono block characters
    """

    def __init__(self, oled):
        self.oled = oled

        # Use the Arvo title font already loaded in oled.py (we'll ensure it exists)
        self.title_font = getattr(oled, "font_title", None) or getattr(oled, "font_large", None) or oled.font

        # DejaVuSansMono is present on Raspberry Pi OS / Debian by default
        self.mono_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            14
        )

    def show(self, duration=2.5, fps=12):
        """
        Show a boot screen with a growing progress bar for `duration` seconds.
        Keeps flicker low by:
          - drawing title once
          - only clearing/redrawing the bar area each frame
        """
        w, h = self.oled.width, self.oled.height

        # --- layout ---
        title = "airBuddy"

        # Compute title placement
        tw, th = self.oled.text_size(title, self.title_font)
        title_y = 0
        title_x = (w - tw) // 2

        # Bar placement (below title)
        bar_y = title_y + th + 10

        # Determine how many mono "blocks" fit across the screen nicely
        block_char = "█"
        space_char = " "
        bw, bh = self.oled.text_size(block_char, self.mono_font)

        # Keep margins so it looks clean
        left_margin = 10
        right_margin = 10
        usable_w = w - left_margin - right_margin

        blocks_total = max(8, usable_w // bw)  # at least 8 blocks

        # Bar text position centered
        bar_text_w = blocks_total * bw
        bar_x = (w - bar_text_w) // 2

        # --- draw title once ---
        self.oled.clear()
        self.oled.draw.text((title_x, title_y), title, font=self.title_font, fill=255)
        self.oled.oled.image(self.oled.image)
        self.oled.oled.show()

        # --- animate bar ---
        frames = max(1, int(duration * fps))
        bar_clear_pad = 2  # extra pixels around the bar text when clearing

        # area to clear for bar each frame (a rectangle)
        bar_h = bh + bar_clear_pad * 2
        bar_top = max(0, bar_y - bar_clear_pad)
        bar_bottom = min(h, bar_y + bh + bar_clear_pad)

        for i in range(frames + 1):
            progress = i / frames
            filled = int(progress * blocks_total)

            bar_str = (block_char * filled) + (space_char * (blocks_total - filled))

            # Clear only the bar region (not the whole screen)
            self.oled.draw.rectangle((0, bar_top, w, bar_bottom), outline=0, fill=0)

            # Draw updated bar
            self.oled.draw.text((bar_x, bar_y), bar_str, font=self.mono_font, fill=255)

            self.oled.oled.image(self.oled.image)
            self.oled.oled.show()

            time.sleep(1 / fps)
