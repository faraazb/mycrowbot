import asyncio
import logging
import os
import re
import sys
import time
import config

import telethon
from telethon import TelegramClient
# from helper import Selector, Restrict
from handler import Student, Admin
# from mydatabase import Datman
# db = Datman()
import logging
logging.basicConfig(level=logging.WARNING)

api_id = config.api_id
api_hash = config.api_hash
bot = TelegramClient(config.bot_id, api_id, api_hash)
bot.parse_mode = 'html'
std = Student(bot)
adm = Admin(bot)
# select = Selector(bot)
# clear = Restrict(bot)
# std.add_handlers()
print('handlers added..')
# adm.add_handlers()

bot.start(bot_token=config.bot_token)
bot.run_until_disconnected()
