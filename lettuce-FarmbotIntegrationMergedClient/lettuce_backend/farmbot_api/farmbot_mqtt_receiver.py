from .mqtt_client import MqttClient


import json


class FarmbotMqttReceiver(MqttClient):
    def __init__(self, farmbot):
        super().__init__(farmbot.token_manager.get_username(),
                         farmbot.token_manager.get_token(),
                         farmbot.token_manager.get_host()
                         )
        self.farmbot = farmbot

        self.status_chan = farmbot.topics["status"]
        self.logs_chan = farmbot.topics["logs"]
        self.incoming_chan = farmbot.topics["from_device"]
        self.outgoing_chan = farmbot.topics["from_clients"]

        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._handle_message

    def receive(self):
        self.mqtt_client.loop_forever()

    def _on_connect(self, *_args):
        self.mqtt_client.subscribe(self.status_chan)
        self.mqtt_client.subscribe(self.logs_chan)
        self.mqtt_client.subscribe(self.incoming_chan)
        self.mqtt_client.subscribe(self.outgoing_chan)

    def _handle_message(self, client, userdata, message):
        if message.topic == self.status_chan:
            self.handle_status(json.loads(message.payload))

        if message.topic == self.logs_chan:
            self.handle_log(json.loads(message.payload))

        if message.topic == self.incoming_chan:
            self.unpack_response(json.loads(message.payload))

    def handle_status(self, message):
        self.farmbot.update_state(message)

    def handle_log(self, message):
        self.farmbot.update_log(message)

    def unpack_response(self, message):
        # print("on from_device: {}".format(message))
        pass
