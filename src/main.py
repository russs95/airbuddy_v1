import time
import random

from ui.oled import OLED
from ui.spinner import Spinner
from input.button import AirBuddyButton


def fake_readings():
    """
    Generate plausible placeholder readings.
    We'll swap this out with real sensor reads later.
    """
    temp_c = round(random.uniform(24.0, 30.5), 1)
    eco2_ppm = int(random.choice([650, 720, 840, 980, 1100, 1350]))
    tvoc_ppb = int(random.choice([35, 60, 120, 180, 260, 420]))

    if eco2_ppm < 800:
        rating = "GOOD"
    elif eco2_ppm < 1200:
        rating = "OK"
    else:
        rating = "POOR"

    return temp_c, eco2_ppm, tvoc_ppb, rating


def main():
    oled = OLED()
    spinner = Spinner(oled)
    btn = AirBuddyButton(gpio_pin=17)

    while True:
        oled.show_waiting("Waiting for button")
        btn.wait_for_press()
        time.sleep(0.08)  # debounce cushion

        spinner.spin(duration=6, label="Sampling air")

        temp_c, eco2_ppm, tvoc_ppb, rating = fake_readings()
        oled.show_results(temp_c, eco2_ppm, tvoc_ppb, rating=rating)

        time.sleep(10)  # hold results
        oled.clear()


if __name__ == "__main__":
    main()
