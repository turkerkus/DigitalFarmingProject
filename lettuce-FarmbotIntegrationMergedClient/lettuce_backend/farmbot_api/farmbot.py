from .farmbot_mqtt_publisher import FarmbotMqttPublisher
from .farmbot_mqtt_receiver import FarmbotMqttReceiver
from .farmbot_token_manager import FarmbotTokenManager
from .farmbot_state_manager import FarmbotStateManager
from .farmbot_log_manager import FarmbotLogManager
from .wrapper import CeleryWrapper
from .wrapper import RpcWrapper

import threading
import logging
from time import sleep


def generate_topic_names(username):
    topics = {"from_clients": "bot/{}/from_clients".format(username),
              "from_device": "bot/{}/from_device".format(username),
              "status": "bot/{}/status".format(username),
              "logs": "bot/{}/logs".format(username)
              }
    return topics


class Farmbot:
    def __init__(self, farmbot_name: str, login):

        self.token_manager = FarmbotTokenManager(login, farmbot_name)

        self.name = farmbot_name
        self.topics = generate_topic_names(self.token_manager.get_username())
        self.current_target_to_move = (0, 0, 0)
        self._first_command_sent = False

        self._mqtt_publisher = FarmbotMqttPublisher(self)
        self._mqtt_receiver = FarmbotMqttReceiver(self)
        self._celery_wrapper = CeleryWrapper()
        self._rpc_wrapper = RpcWrapper()
        self._state_manager = FarmbotStateManager()
        self._log_manager = FarmbotLogManager()
        self.logger = logging.getLogger("farmbot_api.Farmbot")

        self._status_thread = threading.Thread(target=self._mqtt_receiver.receive)

    def connect(self):
        """
        Attempt to connect to the MQTT broker.
        """
        self._mqtt_receiver.connect()
        self._mqtt_publisher.connect()
        self._status_thread.start()
        self.logger.info("connected to {}".format(self.name))

    def disconnect(self):
        """
        Disconnect from Farmbot.
        """

        self._mqtt_publisher.disconnect()
        self._mqtt_receiver.disconnect()
        self.logger.info("disconnected from {}".format(self.name))

    def position(self):
        """
        Convenience method to return the farmbot's current location
        as an (x, y, z) tuple.
        """
        position = self.get_state()["location_data"]["position"]
        x = position["x"]
        y = position["y"]
        z = position["z"]
        return x, y, z

    def move_absolute(self, x, y, z, off_x=0, off_y=0, off_z=0, speed=100):
        """
        Move to an absolute XYZ coordinate at a speed percentage (default speed: 100%).
        """

        instruction = "move_absolute"
        parameters = {"x": x, "y": y, "z": z, "off_x": off_x, "off_y": off_y, "off_z": off_z, "speed": speed}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(x, y, z))

    def send_message(self, message, message_type="info"):
        """
        Send a log message.
        """

        instruction = "send_message"
        parameters = {"message": message, "message_type": message_type}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def emergency_lock(self):
        """
        Perform an emergency stop, thereby preventing any
        motor movement until `emergency_unlock()` is called.
        """

        instruction = "emergency_lock"
        parameters = {}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def emergency_unlock(self):
        """
        Unlock the Farmduino, allowing movement of previously
        locked motors.
        """

        instruction = "emergency_unlock"
        parameters = {}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def find_home(self, speed=100):
        """
        Find the home (0) position for all axes.
        """

        if self.name in ["bot", "bot1", "bot2", "bot3", "bot4", ]:
            raise ValueError("You cannot use find_home on the fake farmbot")

        instruction = "find_home"
        parameters = {"speed": speed}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(0, 0, 0))

    def find_length(self, axis="all"):
        """
        Move to the end of each axis until a stall is detected,
        then set that distance as the maximum length.
        """

        if self.name in ["bot", "bot1", "bot2", "bot3", "bot4", ]:
            raise ValueError("You cannot use find_length on the fake farmbot")

        instruction = "calibrate"
        parameters = {"axis": axis}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def go_to_home(self, axis="all", speed=100):
        """
        Move to the home position for a given axis at a
        particular speed.
        """

        instruction = "home"
        parameters = {"speed": speed, "axis": axis}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(0, 0, 0))

    def move_relative(self, x, y, z, speed=100):
        """
        Move to a relative XYZ offset from the device's current
        position at a speed percentage (default speed: 100%).
        """

        instruction = "move_relative"
        parameters = {"x": x, "y": y, "z": z, "speed": speed}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(x, y, z), relative=True)

    def take_photo(self):
        """
        Snap a photo and send to the API for post-processing.
        """

        instruction = "take_photo"
        parameters = {}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def toggle_pin(self, pin_number):
        """
        Reverse the value of a digital pin.
        """

        instruction = "toggle_pin"
        parameters = {"pin_number": pin_number}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def read_pin(self, pin_number, pin_mode="digital"):
        """
        Read a pin
        """

        instruction = "read_pin"
        parameters = {"pin_number": pin_number, "pin_mode": pin_mode}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    def write_pin(self, pin_number, pin_value, pin_mode="digital"):
        """
        Write to a pin
        """

        instruction = "write_pin"
        parameters = {"pin_number": pin_number, "pin_value": pin_value, "pin_mode": pin_mode}

        celery_blocks = [self._celery_wrapper.wrap_celery_instruction(instruction, parameters)]
        self._send_farmbot_command(celery_blocks)

    ###############################################
    # extra stuff that cant be in lettuce farmbot #
    ###############################################

    def get_state(self):
        return self._state_manager.get_state()

    def update_state(self, new_state):
        self._state_manager.update_state(new_state)

    def get_log(self):
        return self._log_manager.get_log()

    def update_log(self, log_message):
        self._log_manager.update_log(log_message)

    def _send_farmbot_command(self, celery_blocks):
        message = self._rpc_wrapper.wrap_rpc_message(celery_blocks, label="from_lettuce_backend")
        self.logger.info(message)
        self._mqtt_publisher.publish(message)

    def _wait_on_current_target_of_move(self, target, relative=False):
        if relative:
            if not self._first_command_sent:
                self.current_target_to_move = self.position()
                self._first_command_sent = True

            x_current, y_current, z_current = self.current_target_to_move
            x_relative, y_relative, z_relative = target
            target = (x_current+x_relative, y_current+y_relative, z_current+z_relative)

        self.current_target_to_move = target
        x_target, y_target, z_target = target
        while True:
            x_current, y_current, z_current = self.position()
            div_x = abs(x_target - x_current)
            div_y = abs(y_target - y_current)
            div_z = abs(z_target - z_current)
            if (div_x < 1) and (div_y < 1) and (div_z < 1):
                while True:
                    first_value = not self.get_state()["informational_settings"]["busy"]
                    sleep(0.5)
                    second_value = not self.get_state()["informational_settings"]["busy"]
                    if first_value and second_value:
                        return 0
                    sleep(0.5)
            sleep(0.5)
