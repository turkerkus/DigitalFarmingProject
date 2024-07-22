from farmbot_api.lettuce_farmbot import LettuceFarmbot
from farmbot_api.json_tools import read_json
from logging_config import setup_logging

from time import sleep


def demo_picup_return_tools(bot, activ_return, safe_tool_handling):
    bot.picup_watering_nozzle(safe_tool_handling)
    if activ_return:
        bot.return_watering_nozzle(safe_tool_handling)
    bot.picup_seeder(safe_tool_handling)
    if activ_return:
        bot.return_seeder(safe_tool_handling)
    bot.picup_soil_sensor(safe_tool_handling)
    if activ_return:
        bot.return_soil_sensor(safe_tool_handling)
    bot.picup_rotary_tool(safe_tool_handling)
    if activ_return:
        bot.return_rotary_tool(safe_tool_handling)
    bot.picup_weeder(safe_tool_handling)
    bot.return_weeder(safe_tool_handling)


def read_tool_pin(bot):
    while True:
        print(bot.tool_mounted())
        sleep(0.01)


# infos for farmbot (will later be received from frontend)
farmbot_name = "bot1"
login = read_json("/logins.json")[farmbot_name]


# setup logger
setup_logging()

# create a farmbot instance and connect
# make sure to enter a tool_name if a tool is connected!!!
farmbot = LettuceFarmbot(farmbot_name, login, current_tool=None)
farmbot.connect()


# your dev script here:
farmbot.turn_on_led()
farmbot.find_home()

demo_picup_return_tools(farmbot, activ_return=False, safe_tool_handling=False)

farmbot.go_to_home()
farmbot.find_home()
farmbot.turn_off_led()


# this should be the last command in your code
farmbot.disconnect()
