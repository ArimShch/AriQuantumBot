from fluentogram import TranslatorHub, FluentTranslator
from fluent_compiler.bundle import FluentBundle

from pathlib import Path


LOCALES_DIR = Path(__file__).parent.parent / "app" / "bot" / "locales"

def create_translator_hub() -> TranslatorHub:
    locales_map = {
        'en': ('en', 'ru', ), 
        'ru': ('ru', 'en', ), 
    }
    translators = [
        FluentTranslator(
            locale='en', 
            translator=FluentBundle.from_files(
                locale='en-US', filenames=[f'{LOCALES_DIR}/en.ftl', ], 
            )
        ), 
        FluentTranslator(
            locale='ru', 
            translator=FluentBundle.from_files(
                locale='ru-RU', filenames=[f'{LOCALES_DIR}/ru.ftl', ]
            )
        )
    ]

    return TranslatorHub(
        locales_map=locales_map, 
        translators=translators, 
        root_locale='en', 
    )
