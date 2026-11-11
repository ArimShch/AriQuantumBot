import logging
import os
from dataclasses import dataclass
from environs import Env


logger = logging.getLogger(__name__)


@dataclass
class BotSettings:
    token: str
    admin_ids: list[int]
    proxy_url: str | None = None

@dataclass
class DatabaseSettings:
    name: str
    host: str
    port: str 
    user: str 
    password: str
    logging: bool

@dataclass 
class LoggSettings:
    level: str 
    format: str 

@dataclass
class Config:
    bot: BotSettings
    db: DatabaseSettings
    log: LoggSettings


def load_config():
    env = Env()

    env.read_env()

    bot = BotSettings(
        token=env('BOT_TOKEN'),
        admin_ids=env.list('ADMIN_IDS', subcast=int),
        proxy_url=env.str('PROXY_URL', default=None) or None,
    )

    db = DatabaseSettings(
        name=env('POSTGRES_DB'),
        host=env('POSTGRES_HOST'),
        port=env('POSTGRES_PORT'),
        user=env('POSTGRES_USER'),
        password=env('POSTGRES_PASSWORD'),
        logging=env.bool('DEBUG'), 
    )

    log = LoggSettings(
        level=env('LOG_LEVEL'),
        format=env('LOG_FORMAT'),
    )

    logger.info('Configs loaded successfully')

    return Config(
        bot=bot,
        db=db,
        log=log,
    )


