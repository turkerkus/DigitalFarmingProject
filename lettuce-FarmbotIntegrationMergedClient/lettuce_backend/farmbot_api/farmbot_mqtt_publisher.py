from .mqtt_client import MqttClient

import json
from time import sleep


class FarmbotMqttPublisher(MqttClient):
    def __init__(self, farmbot):
        super().__init__(farmbot.token_manager.get_username(),
                         farmbot.token_manager.get_token(),
                         farmbot.token_manager.get_host()
                         )

        self.min_wait_time_between_messages = 0.5
        self._publishing_topic = farmbot.topics["from_clients"]

    def publish(self, message):
        message = json.dumps(message)
        self.mqtt_client.publish(self._publishing_topic, message, 0)
        sleep(self.min_wait_time_between_messages)
