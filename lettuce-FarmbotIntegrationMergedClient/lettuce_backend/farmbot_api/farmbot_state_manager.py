import threading
from time import sleep


def test_if_state_is_valid(state):
    def check_nested_key(x, keys):
        for key in keys:
            try:
                x = x[key]
            except KeyError:
                return None
        return x

    eval_elements = ["", {}, [], None]

    attributes_to_check = [
        ("location_data", "position", "x"),
        ("location_data", "position", "y"),
        ("location_data", "position", "z"),
        ("location_data", "axis_states", "x"),
        ("location_data", "axis_states", "y"),
        ("location_data", "axis_states", "z"),
        ("pins", "7", "value"),
        ("pins", "8", "value"),
        ("pins", "9", "value"),
        ("pins", "38", "value"),
        ("informational_settings", "busy"),
        ("informational_settings", "idle")
    ]

    for attribute in attributes_to_check:
        if check_nested_key(state, attribute) in eval_elements:
            return False
    return True


class FarmbotStateManager:
    def __init__(self):
        self.__state = None
        self.__state_is_valid = False
        self.lock = threading.Lock()

    def update_state(self, new_state):
        with self.lock:
            self.__state = new_state
            self.__state_is_valid = test_if_state_is_valid(new_state)

    def get_state(self):
        while True:
            with self.lock:
                if self.__state_is_valid:
                    return self.__state
            sleep(0.01)
