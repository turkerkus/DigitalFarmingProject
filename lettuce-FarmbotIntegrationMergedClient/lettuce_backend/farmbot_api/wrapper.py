class RpcWrapper:
    def wrap_rpc_message(self, body: list, label="label123", priority=500):
        message = {
            "kind": "rpc_request",
            "args": {"label": label, "priority": priority},
            "body": body
        }
        return message


class CeleryWrapper:
    def wrap_celery_instruction(self, kind: str, parameters: dict):

        match kind:
            case "move_absolute":
                args = {
                    "location": {"kind": "coordinate", "args": {"x": parameters["x"],
                                                                "y": parameters["y"],
                                                                "z": parameters["z"]}},
                    "offset": {"kind": "coordinate", "args": {"x": parameters["off_x"],
                                                              "y": parameters["off_y"],
                                                              "z": parameters["off_z"]}},
                    "speed": parameters["speed"]
                }
            case "send_message":
                args = {
                    "message": parameters["message"],
                    "message_type": parameters["message_type"]
                }
            case "emergency_lock":
                args = {}
            case "emergency_unlock":
                args = {}
            case "find_home":
                args = {
                    "axis": "all",
                    "speed": parameters["speed"]
                }
            case "calibrate":
                args = {
                    "axis": parameters["axis"]
                }

            case "home":
                args = {
                    "speed": parameters["speed"],
                    "axis": parameters["axis"]
                }
            case "move_relative":
                args = {
                    "x": parameters["x"],
                    "y": parameters["y"],
                    "z": parameters["z"],
                    "speed": parameters["speed"]
                }
            case "take_photo":
                args = {}
            case "toggle_pin":
                args = {
                    "pin_number": parameters["pin_number"]
                }
            case "read_pin":
                modes = {"digital": 0, "analog": 1}
                args = {
                    "label": "pin" + str(parameters["pin_number"]),
                    "pin_mode": modes[parameters["pin_mode"]],
                    "pin_number": parameters["pin_number"]
                }
            case "write_pin":
                modes = {"digital": 0, "analog": 1}
                args = {
                    "pin_mode": modes[parameters["pin_mode"]],
                    "pin_number": parameters["pin_number"],
                    "pin_value": parameters["pin_value"]
                }
            case _:
                raise NotImplementedError("The celery_wrapper does not know the instruction '{}'.".format(kind))

        body = {"kind": kind, "args": args}

        return body
