from gpiozero import Button


class AirBuddyButton:
    def __init__(self, gpio_pin=17):
        # pull_up=True means button to GND; pressed = LOW
        self.button = Button(gpio_pin, pull_up=True, bounce_time=0.05)

    def wait_for_press(self):
        self.button.wait_for_press()
