import threading
from time import sleep


class FarmbotLogManager:
    def __init__(self):
        self.__last_log_message = None
        self.__last_log_message_is_valid = False
        self.__is_tool_verification = False
        self.__lock_of_log = threading.Lock()  # lock 1!
        self.__lock_of_is_tool_verification = threading.Lock()  # lock 2!

    def update_log(self, log_message):
        with self.__lock_of_log:  # lock 1
            self.__last_log_message = log_message
            self.__last_log_message_is_valid = self._test_if_log_is_valid(log_message)

    def get_log(self):
        while True:
            with self.__lock_of_log:  # lock 1
                if self.__last_log_message_is_valid:
                    return self.__last_log_message
            sleep(0.01)

    def _test_if_log_is_valid(self, log_message):

        def check_nested_key(x, keys):
            if type(keys) is str:
                return x[keys]

            for key in keys:
                try:
                    x = x[key]
                except KeyError:
                    return None
            return x

        eval_elements = ["", {}, [], None]

        attributes_to_check = [
            "message",
            "type"
        ]

        for attribute in attributes_to_check:
            if check_nested_key(log_message, attribute) in eval_elements:
                return False

        self._test_if_tool_verification_message(log_message)

        return True

    def _test_if_tool_verification_message(self, log_message):
        with self.__lock_of_is_tool_verification:  # lock 2
            if log_message["message"].startswith('The Tool Verification sensor value is '):
                self.__is_tool_verification = True
            else:
                self.__is_tool_verification = False

    def get_tool_verification_sensor_value(self):
        while True:
            message = self.get_log()["message"]
            with self.__lock_of_is_tool_verification:  # lock 2
                if self.__is_tool_verification:
                    if message == 'The Tool Verification sensor value is 1 (digital)':
                        return 1
                    elif message == 'The Tool Verification sensor value is 0 (digital)':
                        return 0
                    else:
                        raise ValueError("The verification sensor value message is wrong: {}".format(self.__last_log_message))
            sleep(0.01)
