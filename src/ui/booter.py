# src/ui/booter.py
import time
from PIL import ImageFont


class Booter:
    """
    Boot screen:
      - Title: "airBuddy" using oled.font_title (Arvo 22)
      - Loading bar: DejaVuSansMono block characters
      - Bar positioned to match idle screen "Waiting for button" line (y=34)
    """

    def __init__(self, oled):
        self.oled = oled

        # Use fonts already loaded in oled.py
        self.title_font = getattr(oled, "font_title", None) or ImageFont.load_default()
        self.small_font = getattr(oled, "font_small", None) or ImageFont.load_default()

        # Smaller mono font keeps the bar height closer to the idle text line
        try:
            self.mono_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                8
            )
        except Exception:
            self.mono_font = ImageFont.load_default()

    # ---------- internal helpers ----------

    def _text_size(self, text, font):
        """
        Measure text using Pillow's textbbox (no dependency on OLED.text_size()).
        """
        bbox = self.oled.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    # ---------- main ----------

    def show(self, duration=2.5, fps=12):
        """
        Show a boot screen with a growing progress bar for `duration` seconds.
        Keeps flicker low by:
          - drawing title once
          - only clearing/redrawing the bar area each frame
        """
        w, h = self.oled.width, self.oled.height

        title = "airBuddy"

        # Title position: match your idle screen wordmark position
        # (idle uses draw_centered("airBuddy", 10, font_title))
        title_y = 10

        # Draw title once
        self.oled.clear()
        self.oled.draw_centered(title, title_y, self.title_font)
        self.oled.oled.image(self.oled.image)
        self.oled.oled.show()

        # Bar position: align to the same y as idle "Waiting for button" line
        # (idle uses draw_centered(line, 34, font_small))
        idle_line_y = 34

        # Use block characters to build a text bar
        block_char = "█"
        space_char = " "

        bw, bh = self._text_size(block_char, self.mono_font)

        # Determine total blocks across, with side margins
        left_margin = 10
        right_margin = 10
        usable_w = w - left_margin - right_margin
        blocks_total = max(10, usable_w // max(1, bw))

        bar_str_empty = (space_char * blocks_total)
        bar_text_w = blocks_total * bw
        bar_x = (w - bar_text_w) // 2

        # Center the bar vertically relative to the idle text line:
        # idle line is drawn at y=34; we want bar to sit in same visual band.
        # So compute bar_y so its text bbox centers around idle_line_y + (small text height/2).
        _, sh = self._text_size("Waiting", self.small_font)
        baseline_center_y = idle_line_y + (sh // 2)
        bar_y = max(0, baseline_center_y - (bh // 2))

        # Only clear a tight rectangle around the bar
        pad = 2
        bar_top = max(0, bar_y - pad)
        bar_bottom = min(h, bar_y + bh + pad)

        frames = max(1, int(duration * fps))

        for i in range(frames + 1):
            progress = i / frames
            filled = int(progress * blocks_total)
            bar_str = (block_char * filled) + (space_char * (blocks_total - filled))

            # Clear only bar region
            self.oled.draw.rectangle((0, bar_top, w, bar_bottom), outline=0, fill=0)

            # Draw bar
            self.oled.draw.text((bar_x, bar_y), bar_str, font=self.mono_font, fill=255)

            self.oled.oled.image(self.oled.image)
            self.oled.oled.show()

            time.sleep(1 / fps)
