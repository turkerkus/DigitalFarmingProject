# from .farmbot import Farmbot
# from .json_tools import read_json
# import asyncio
# import websockets
#
# import logging
#
# from time import sleep
# import numpy as np
#
#
# class LettuceFarmbot(Farmbot):
#     def __init__(self,
#                  farmbot_name: str,
#                  login: dict,
#                  safe_height=None,
#                  seeding_height=None,
#                  water_height=None,
#                  weeding_height=None,
#                  current_tool=None
#                  ):
#         super().__init__(farmbot_name, login)
#
#         self.safe_height = safe_height or -300  # -300 is the absolute minimum. If plants grow it has to be higher
#         self.seeding_height = seeding_height or -510
#         self.water_height = water_height or -200
#         self.weeding_height = weeding_height or -530
#
#         self.current_tool = current_tool or None
#         self.tool_positions = read_json("./farmbot_api/positions.json")
#         self.valid_tool_names = ["seeder", "watering_nozzle", "soil_sensor", "rotary_tool", "weeder"]
#
#         self.status = "offline"
#         self.valid_status_names = ["fetching",
#                                    "moving",
#                                    "moving to seeding position",
#                                    "moving to watering position",
#                                    "seeding",
#                                    "ready",
#                                    "offline",
#                                    "watering"]
#
#     async def connect(self):
#         await super().connect()
#         self.update_status("ready")
#         logging.debug("LettuceFarmbot Connected and Ready")
#
#
#     async def disconnect(self):
#         await super().disconnect()
#         self.update_status("offline")
#         logging.debug("LettuceFarmbot Disconnected and Offline")
#
#
#     def move_absolute_safe_height(self, x, y, z, speed=100):
#         x_start, y_start, z_start = self.position()
#         if z_start > self.safe_height:
#             z_move_height = z_start
#         else:
#             z_move_height = self.safe_height
#
#         # move upwards to save height
#         # move to position x, y, z=self.save_height
#         # move down to x, y, z
#         celery_blocks = [self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x_start,
#                                                                                         "y": y_start,
#                                                                                         "z": z_move_height,
#                                                                                         "off_x": 0,
#                                                                                         "off_y": 0,
#                                                                                         "off_z": 0,
#                                                                                         "speed": speed}),
#                          self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x,
#                                                                                         "y": y,
#                                                                                         "z": z_move_height,
#                                                                                         "off_x": 0,
#                                                                                         "off_y": 0,
#                                                                                         "off_z": 0,
#                                                                                         "speed": speed}),
#                          self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x,
#                                                                                         "y": y,
#                                                                                         "z": z,
#                                                                                         "off_x": 0,
#                                                                                         "off_y": 0,
#                                                                                         "off_z": 0,
#                                                                                         "speed": speed})]
#         message = self._rpc_wrapper.wrap_rpc_message(celery_blocks, label="from_lettuce_backend")
#         if self.status not in ["fetching",
#                                "moving to seeding position",
#                                "moving to watering position",
#                                "seeding",
#                                "watering"
#                                ]:
#             self.update_status("moving")
#
#         print(message)
#         self._mqtt_publisher.publish(message)
#         self._wait_on_current_target_of_move(target=(x, y, z))
#
#     def move_circle(self, x_center, y_center, z_center, radius, num_points=20, speed=100):
#         celery_blocks = []
#
#         t = np.linspace(0, 2*np.pi, num_points)
#         x = radius * np.cos(t) + x_center
#         y = radius * np.sin(t) + y_center
#
#         parameters = {"x": 0, "y": 0, "z": z_center, "off_x": 0, "off_y": 0, "off_z": 0, "speed": speed}
#
#         for i in range(len(t)):
#             parameters["x"] = x[i]
#             parameters["y"] = y[i]
#             celery_blocks.append(self._celery_wrapper.wrap_celery_instruction("move_absolute", parameters))
#
#         if self.status not in ["fetching",
#                                "moving to seeding position",
#                                "moving to watering position",
#                                "seeding",
#                                "watering"
#                                ]:
#             self.update_status("moving")
#         message = self._rpc_wrapper.wrap_rpc_message(celery_blocks, label="from_lettuce_backend")
#         print(message)
#         self._mqtt_publisher.publish(message)
#         self._wait_on_current_target_of_move(target=(x[-1], y[-1], z_center))
#
#         if self.status == "moving":
#             self.update_status("ready")
#
#     def turn_on_led(self):
#         self.write_pin(7, 1)
#
#     def turn_off_led(self):
#         self.write_pin(7, 0)
#
#     def turn_on_water_nozzle(self):
#         self.write_pin(8, 1)
#
#     def turn_off_water_nozzle(self):
#         self.write_pin(8, 0)
#
#     def turn_on_vacuum(self):
#         self.write_pin(9, 1)
#
#     def turn_off_vacuum(self):
#         self.write_pin(9, 0)
#
#     def turn_on_plant_lights(self):
#         self.write_pin(38, 1)
#
#     def turn_off_plant_lights(self):
#         self.write_pin(38, 0)
#
#     def _check_if_tool_name_is_valid(self, tool_name):
#         if tool_name not in self.valid_tool_names:
#             raise KeyError("The tool '{}' does not exist.".format(tool_name))
#
#     async def picup_tool(self, tool_name):
#         self._check_if_tool_name_is_valid(tool_name)
#         logging.debug(f"Picking up tool: {tool_name}")
#
#         if self.current_tool is not None:
#             # check if it is the needed tool
#             if self.current_tool == tool_name:
#                 return
#             else:
#                 self.return_tool(self.current_tool)
#         logging.debug("Starting tool pickup")
#         self.move_absolute_safe_height(self.tool_positions[tool_name]["x"],
#                                        self.tool_positions[tool_name]["y"],
#                                        self.tool_positions[tool_name]["z"])
#         logging.debug("Picked up")
#         self.move_relative(-115, 0, 0)
#         logging.debug(f"Reached")
#         await asyncio.sleep(3)
#         self.current_tool = tool_name
#
#     async def return_tool(self, tool_name):
#         self._check_if_tool_name_is_valid(tool_name)
#         logging.debug(f"Returning tool: {tool_name}")
#         await asyncio.sleep(3)
#         self.move_absolute_safe_height(self.tool_positions[tool_name]["x"] - 100,
#                                        self.tool_positions[tool_name]["y"],
#                                        self.tool_positions[tool_name]["z"])
#
#         self.move_relative(+100, 0, 0)
#         self.move_absolute_safe_height(self.tool_positions[tool_name]["x"],
#                                        self.tool_positions[tool_name]["y"],
#                                        self.safe_height)
#         self.current_tool = None
#
#     def picup_watering_nozzle(self):
#         self.picup_tool("watering_nozzle")
#
#     def return_watering_nozzle(self):
#         self.return_tool("watering_nozzle")
#
#     def picup_seeder(self):
#         self.picup_tool("seeder")
#
#     def return_seeder(self):
#         self.return_tool("seeder")
#
#     def picup_soil_sensor(self):
#         self.picup_tool("soil_sensor")
#
#     def return_soil_sensor(self):
#         self.return_tool("soil_sensor")
#
#     def picup_rotary_tool(self):
#         self.picup_tool("rotary_tool")
#
#     def return_rotary_tool(self):
#         self.return_tool("rotary_tool")
#
#     def picup_weeder(self):
#         self.picup_tool("weeder")
#
#     def return_weeder(self):
#         self.return_tool("weeder")
#
#     def water(self, x, y, z, ml):
#         seconds_to_water = ml / 10  # 10 ml / sec
#
#         self.update_status("moving to watering position")
#         self.move_absolute_safe_height(x, y, z)
#
#         self.update_status("watering")
#         self.turn_on_water_nozzle()
#         sleep(seconds_to_water)
#         self.turn_off_water_nozzle()
#
#     def execute_watering_jobs(self, watering_jobs):
#         self.picup_tool("watering_nozzle")
#
#         for watering_job in watering_jobs:
#             self.water(watering_job["x"], watering_job["y"], self.water_height, watering_job["volume"])
#
#         self.return_tool("watering_nozzle")
#         self.update_status("ready")
#
#     def _picup_seed(self):
#         self.update_status("fetching")
#         self.move_absolute_safe_height(self.tool_positions["seeder_bin"]["x"],
#                                        self.tool_positions["seeder_bin"]["y"],
#                                        self.tool_positions["seeder_bin"]["z"])
#         self.turn_on_vacuum()
#
#     def _place_seed(self, x, y):
#         self.update_status("moving to seeding position")
#         self.move_absolute_safe_height(x, y, self.safe_height)
#         self.update_status("seeding")
#         self.move_absolute_safe_height(x, y, self.seeding_height)
#         self._wait_on_current_target_of_move(self.current_target_to_move)
#         self.turn_off_vacuum()
#         self.move_absolute(x, y, self.safe_height)
#
#     def seed(self, x, y):
#         self._picup_seed()
#         self._place_seed(x, y)
#
#     async def execute_seeding_job(self, seeding_jobs):
#             logging.debug("Starting Seeding Job")
#             await self.picup_tool("seeder")
#             for seeding_job in seeding_jobs:
#                 await self.seed(seeding_job["x"], seeding_job["y"])
#             await self.return_tool("seeder")
#             self.update_status("ready")
#             logging.debug("Seeding Job Completed")
#
#     def _check_if_status_name_is_valid(self, status_name):
#         if status_name not in self.valid_status_names:
#             raise KeyError("The status '{}' does not exist.".format(status_name))
#
#     def update_status(self, new_status):
#         print("test")
# #         self._check_if_status_name_is_valid(new_status)
# #         self.status = new_status
# #         self.send_message(new_status)
# #         async def handler(websocket, path):
# #             while True:
# #                 message = "Hello from Python server!"
# #                 await websocket.send(new_status)
# #                 await asyncio.sleep(1)
# #
# #         start_server = websockets.serve(handler, "localhost", 6789)
# #
# #         asyncio.get_event_loop().run_until_complete(start_server)
# #         asyncio.get_event_loop().run_forever()


from .farmbot import Farmbot
from .json_tools import read_json
import asyncio
import websockets
from time import sleep
import numpy as np


class LettuceFarmbot(Farmbot):
    status = "offline"

    def __init__(self,
                 farmbot_name: str,
                 login: dict,
                 safe_height=None,
                 seeding_height=None,
                 watering_height=None,
                 weeding_height=None,
                 seeder_soil_height=None,
                 current_tool=None
                 ):
        super().__init__(farmbot_name, login)

        self.safe_height = safe_height or -300  # -300 is the absolute minimum. If plants grow it has to be higher
        self.seeding_height = seeding_height or -510
        self.watering_height = watering_height or -200
        self.weeding_height = weeding_height or -530
        self.seeder_soil_height = seeder_soil_height or -495  # soil_height with seeder mounted (has to be checked if the value is fine)

        self.current_tool = current_tool or None
        self.tool_positions = read_json("./farmbot_api/positions.json")
        self.valid_tool_names = ["seeder", "watering_nozzle", "soil_sensor", "rotary_tool", "weeder"]

        self.valid_status_names = {"fetching seed",
                                   "moving",
                                   "moving to seeding position",
                                   "moving to watering position",
                                   "seeding",
                                   "ready",
                                   "offline",
                                   "watering",
                                   "picking up tool",
                                   "returning tool",
                                   "emergency lock"}

    ###########################################
    # override some methods from parent class #
    ###########################################

    def connect(self):
        super().connect()
        self.update_status("ready")

    def disconnect(self):
        self.update_status("offline")
        super().disconnect()

    def go_to_home(self, axis="all", speed=100):
        if axis != "all":
            raise NotImplementedError("Sry you can currently just do this for all axis")

        self.move_absolute_safe_height(0, 0, 0, speed=speed)

    def emergency_lock(self):
        super().emergency_lock()
        self.update_status("emergency lock")

    def emergency_unlock(self):
        super().emergency_unlock()
        self.update_status("ready")

    ###############
    # Own methods #
    ###############

    def move_absolute_safe_height(self, x, y, z, speed=100):
        x_start, y_start, z_start = self.position()

        if x == x_start and y == y_start and z == z_start:
            return

        if z_start > self.safe_height:
            z_move_height = z_start
        else:
            z_move_height = self.safe_height

        # move upwards to save height
        # move to position x, y, z=self.save_height
        # move down to x, y, z
        celery_blocks = [self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x_start,
                                                                                        "y": y_start,
                                                                                        "z": z_move_height,
                                                                                        "off_x": 0,
                                                                                        "off_y": 0,
                                                                                        "off_z": 0,
                                                                                        "speed": speed}),
                         self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x,
                                                                                        "y": y,
                                                                                        "z": z_move_height,
                                                                                        "off_x": 0,
                                                                                        "off_y": 0,
                                                                                        "off_z": 0,
                                                                                        "speed": speed}),
                         self._celery_wrapper.wrap_celery_instruction("move_absolute", {"x": x,
                                                                                        "y": y,
                                                                                        "z": z,
                                                                                        "off_x": 0,
                                                                                        "off_y": 0,
                                                                                        "off_z": 0,
                                                                                        "speed": speed})]

        if self.status not in self.valid_status_names - {"offline", "ready"}:
            self.update_status("moving")

        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(x, y, z))

        if self.status not in self.valid_status_names - {"offline", "ready"}:
            self.update_status("ready")

    def move_circle(self, x_center, y_center, z_center, radius, num_points=20, speed=100):
        celery_blocks = []

        t = np.linspace(0, 2 * np.pi, num_points)
        x = radius * np.cos(t) + x_center
        y = radius * np.sin(t) + y_center

        parameters = {"x": 0, "y": 0, "z": z_center, "off_x": 0, "off_y": 0, "off_z": 0, "speed": speed}

        for i in range(len(t)):
            parameters["x"] = x[i]
            parameters["y"] = y[i]
            celery_blocks.append(self._celery_wrapper.wrap_celery_instruction("move_absolute", parameters))

        if self.status not in self.valid_status_names - {"offline", "ready"}:
            self.update_status("moving")

        self._send_farmbot_command(celery_blocks)
        self._wait_on_current_target_of_move(target=(x[-1], y[-1], z_center))

        if self.status not in self.valid_status_names - {"offline", "ready"}:
            self.update_status("ready")

    def turn_on_led(self):
        self.write_pin(7, 1)

    def turn_off_led(self):
        self.write_pin(7, 0)

    def turn_on_water_nozzle(self):
        self.write_pin(8, 1)

    def turn_off_water_nozzle(self):
        self.write_pin(8, 0)

    def turn_on_vacuum(self):
        self.write_pin(9, 1)

    def turn_off_vacuum(self):
        self.write_pin(9, 0)

    def turn_on_plant_lights(self):
        self.write_pin(38, 1)

    def turn_off_plant_lights(self):
        self.write_pin(38, 0)

    def _check_if_tool_name_is_valid(self, tool_name):
        if tool_name not in self.valid_tool_names:
            raise KeyError("The tool '{}' does not exist.".format(tool_name))

    def _picup_tool(self, tool_name, safe=False):
        self._check_if_tool_name_is_valid(tool_name)

        if safe:
            if self.current_tool is None and self.tool_mounted():
                raise ValueError("The Farmbot thinks no tool is mounted, but the sensor sais a tool is mounted")
            if self.current_tool is not None and not self.tool_mounted():
                raise ValueError("The Farmbot thinks a tool is mounted, but the sensor sais no tool is mounted")

        if self.current_tool is not None:
            # check if it is the needed tool
            if self.current_tool == tool_name:
                return
            else:
                self._return_tool(self.current_tool)

        self.update_status("picking up tool")

        self.move_absolute_safe_height(self.tool_positions[tool_name]["x"],
                                       self.tool_positions[tool_name]["y"],
                                       self.tool_positions[tool_name]["z"])

        self.move_relative(-115, 0, 0)
        self.current_tool = tool_name

        if safe:
            if not self.tool_mounted():
                raise ValueError("There should be a tool mounted but for unknown reasons the sensor can't detect one.")

    def _return_tool(self, tool_name, safe=False):
        self._check_if_tool_name_is_valid(tool_name)

        if safe:
            if not self.tool_mounted():
                raise ValueError("There should be a tool mounted but for unknown reasons the sensor can't detect one.")

        self.update_status("returning tool")

        self.move_absolute_safe_height(self.tool_positions[tool_name]["x"] - 115,
                                       self.tool_positions[tool_name]["y"],
                                       self.tool_positions[tool_name]["z"])

        self.move_relative(+115, 0, 0)
        self.move_absolute_safe_height(self.tool_positions[tool_name]["x"],
                                       self.tool_positions[tool_name]["y"],
                                       self.safe_height)
        self.current_tool = None

        if safe:
            if self.tool_mounted():
                raise ValueError("There should be no tool mounted but for unknown reasons the sensor can detect one.")

    def picup_watering_nozzle(self, safe=False):
        self._picup_tool("watering_nozzle", safe)

    def return_watering_nozzle(self, safe=False):
        self._return_tool("watering_nozzle", safe)

    def picup_seeder(self, safe=False):
        self._picup_tool("seeder", safe)

    def return_seeder(self, safe=False):
        self._return_tool("seeder", safe)

    def picup_soil_sensor(self, safe=False):
        self._picup_tool("soil_sensor", safe)

    def return_soil_sensor(self, safe=False):
        self._return_tool("soil_sensor", safe)

    def picup_rotary_tool(self, safe=False):
        self._picup_tool("rotary_tool", safe)

    def return_rotary_tool(self, safe=False):
        self._return_tool("rotary_tool", safe)

    def picup_weeder(self, safe=False):
        self._picup_tool("weeder", safe)

    def return_weeder(self, safe=False):
        self._return_tool("weeder", safe)

    def _water(self, x, y, ml, watering_height=None):
        seconds_to_water = ml / 10  # 10 ml / sec

        if watering_height is None:
            watering_height = self.watering_height

        self.update_status("moving to watering position")
        self.move_absolute_safe_height(x, y, watering_height)

        self.update_status("watering")
        self.turn_on_water_nozzle()
        sleep(seconds_to_water)
        self.turn_off_water_nozzle()

    def execute_watering_jobs(self, watering_jobs, safe_tool_handling=False):
        self._picup_tool("watering_nozzle", safe_tool_handling)

        for watering_job in watering_jobs:
            try:
                watering_height = watering_job["watering_height"]
            except KeyError:
                watering_height = None
            self._water(watering_job["x"], watering_job["y"], watering_job["volume"], watering_height)

        self._return_tool("watering_nozzle", safe_tool_handling)
        self.update_status("ready")

    def _picup_seed(self):
        self.update_status("fetching seed")
        self.move_absolute_safe_height(self.tool_positions["seeder_bin"]["x"],
                                       self.tool_positions["seeder_bin"]["y"],
                                       self.tool_positions["seeder_bin"]["z"])
        self.turn_on_vacuum()

    def _place_seed(self, x, y, z):
        self.update_status("moving to seeding position")
        self.move_absolute_safe_height(x, y, self.safe_height)
        self.update_status("seeding")
        self.move_absolute_safe_height(x, y, z)
        self._wait_on_current_target_of_move(self.current_target_to_move)
        self.turn_off_vacuum()
        self.move_absolute(x, y, self.safe_height)

    def _seed(self, x, y, seeding_depth=None):
        seeding_z = self._calculate_seeding_depth(seeding_depth)
        self._picup_seed()
        self._place_seed(x, y, seeding_z)

    def _calculate_seeding_depth(self, seeding_depth):
        if seeding_depth is None or seeding_depth > 4 or seeding_depth < 0:
            seeding_z = self.seeding_height
        else:
            seeding_z = self.seeder_soil_height - seeding_depth

        return seeding_z

    def execute_seeding_job(self, seeding_jobs, safe_tool_handling=False):
        self._picup_tool("seeder", safe_tool_handling)

        for seeding_job in seeding_jobs:
            try:
                seeding_depth = seeding_job["seeding_depth"]
            except KeyError:
                seeding_depth = None
            self._seed(seeding_job["x"], seeding_job["y"], seeding_depth)

        self._return_tool("seeder", safe_tool_handling)
        self.update_status("ready")

    def _check_if_status_name_is_valid(self, status_name):
        if status_name not in self.valid_status_names:
            raise KeyError("The status '{}' does not exist.".format(status_name))

    @classmethod
    def update_status(cls, new_status):
        cls.status = new_status
        print(f"Status updated to: {new_status}")
#         self._check_if_status_name_is_valid(new_status)
#         self.status = new_status
#         self.send_message(new_status)
#         async def handler(websocket, path):
#             while True:
#                 message = "Hello from Python server!"
#                 await websocket.send(new_status)
#                 await asyncio.sleep(1)
#
#         start_server = websockets.serve(handler, "localhost", 6789)
#
#         asyncio.get_event_loop().run_until_complete(start_server)
#         asyncio.get_event_loop().run_forever()
