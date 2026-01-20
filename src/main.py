import time

from ui.oled import OLED
from ui.spinner import Spinner
from input.button import AirBuddyButton


def main():
    oled = OLED()
    spinner = Spinner(oled)
    btn = AirBuddyButton(gpio_pin=17)

    # Idle loop: wait for button, then spin, then return to waiting
    while True:
        oled.show_waiting("Waiting for button")
        btn.wait_for_press()

        # tiny pause to avoid bounce-trigger “double press”
        time.sleep(0.08)

        spinner.spin(duration=6, label="Sampling air")

        # After spinner, for now go back to waiting immediately
        # (Later: show sensor values for 10 seconds)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
