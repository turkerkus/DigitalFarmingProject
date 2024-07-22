from farmbot_api.lettuce_farmbot import LettuceFarmbot
from farmbot_api.json_tools import read_json
from logging_config import setup_logging

from time import sleep


# infos for farmbot (will later be received from frontend)
farmbot_name = "farmbot"
login = read_json("kjell_kram/logins/logins.json")[farmbot_name]


# setup logger
setup_logging()

# create a farmbot instance and connect
# make sure to enter a tool_name if a tool is connected!!!
farmbot = LettuceFarmbot(farmbot_name, login, current_tool=None)
farmbot.connect()


# your dev script here:
#farmbot.turn_on_plant_lights()
#farmbot.turn_on_led()
#(farmbot.find_home()
#farmbot.picup_weeder())
#farmbot.move_absolute_safe_height(2000, 1000, farmbot.weeding_height)

farmbot.execute_seeding_job(read_json("kjell_kram/demo_seeding_jobs.json"))
farmbot.execute_watering_jobs(read_json("kjell_kram/watering_jobs.json"))
farmbot.go_to_home()
farmbot.turn_off_led()
farmbot.turn_off_plant_lights()


# this should be the last command in your code
farmbot.disconnect()
