import asyncio
import os
import sys 
import logging 

from app.bot.bot import main
from config.config import Config, load_config


config: Config = load_config()

logging.basicConfig(
    level=config.log.level,
    format=config.log.format,
    style='{',
)

logging.getLogger('app.bot.bot').setLevel(logging.INFO)

if sys.platform.startswith('win') or os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(main(config))