import paho.mqtt.client as mqtt
from time import sleep


class MqttClient:
    def __init__(self, username, token, host):
        self._username = username
        self._token = token
        self._host = host
        self.is_connected = False
        self.mqtt_client = mqtt.Client()

        self._setup_client()

    def _setup_client(self):
        self.mqtt_client.username_pw_set(self._username, self._token)

    def connect(self):
        if self.mqtt_client.connect(self._host) != 0:
            print("Not able to connect to MQTT broker")
            self.is_connected = False
        else:
            self.is_connected = True
        sleep(3)

    def disconnect(self):
        sleep(2)
        self.mqtt_client.disconnect()
        self.is_connected = False
