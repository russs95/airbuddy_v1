import time
import random

from ui.oled import OLED
from ui.spinner import Spinner
from ui.booter import Booter
from input.button import AirBuddyButton


def fake_readings():
    """
    Generate plausible placeholder readings.
    We'll swap this out with real sensor reads later.
    Testing
    """
    temp_c = round(random.uniform(24.0, 30.5), 1)
    eco2_ppm = int(random.choice([650, 720, 840, 980, 1100, 1350]))
    tvoc_ppb = int(random.choice([35, 60, 120, 180, 260, 420]))

    if eco2_ppm < 700:
        rating = "Very good"
    elif eco2_ppm < 900:
        rating = "Good"
    elif eco2_ppm < 1300:
        rating = "Ok"
    else:
        rating = "Poor"

    return temp_c, eco2_ppm, tvoc_ppb, rating


def main():
    oled = OLED()

    # Boot loader screen (title + progress bar)
    Booter(oled).show(duration=2.5, fps=12)

    spinner = Spinner(oled)
    btn = AirBuddyButton(gpio_pin=17)

    while True:
        # Idle
        oled.show_waiting("Waiting for button")
        btn.wait_for_press()
        time.sleep(0.08)  # debounce cushion

        # Spinner
        spinner.spin(duration=6)

        # Fake data (for now)
        temp_c, eco2_ppm, tvoc_ppb, rating = fake_readings()
        oled.show_results(temp_c, eco2_ppm, tvoc_ppb, rating=rating)

        # Hold results
        time.sleep(10)

        # Mood face
        oled.show_face(rating)
        time.sleep(3)

        # Back to idle
        oled.clear()


if __name__ == "__main__":
    main()
