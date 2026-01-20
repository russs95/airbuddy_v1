from ui.oled import OLED
from ui.spinner import Spinner
from input.button import Button


def main():
    oled = OLED()
    spinner = Spinner(oled)
    button = Button(pin=17)

    try:
        while True:
            oled.text([
                "airBuddy v1",
                "",
                "Press button"
            ])

            button.wait_for_press()
            spinner.spin(duration=3)

    except KeyboardInterrupt:
        pass
    finally:
        button.cleanup()
        oled.clear()


if __name__ == "__main__":
    main()

