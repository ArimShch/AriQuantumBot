from aiogram.types import BotCommand

from fluentogram import TranslatorRunner


def get_main_menu_commands(role: str, i18n: TranslatorRunner):
    if role == 'user':
        return [
            BotCommand(
                command='/start',
                description=i18n.cmnd_menu()
            ),        
            BotCommand(
                command='/create_circuit',
                description=i18n.cmnd_create_circuit()
            ),
            BotCommand(
                command='/help', 
                description=i18n.cmnd_help()
            )
        ]
    elif role == 'admin':
        return [
            BotCommand(
                command='/start',
                description=i18n.cmnd_menu()
            ),
            BotCommand(
                command='/create_circuit',
                description=i18n.cmnd_create_circuit()
            ),
            BotCommand(
                command='/help', 
                description=i18n.cmnd_help()
            ),
            BotCommand(
                command='/admin',
                description=i18n.cmnd_admin()
            ),
        ]