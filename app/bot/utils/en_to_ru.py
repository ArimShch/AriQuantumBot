import re
from transliterate import translit

def slugify_filename(text: str) -> str:
    # 1. Переводим кириллицу в транслит (на английский)
    transliterated = translit(text, 'ru', reversed=True)
    
    # 2. Заменяем пробелы и дефисы на нижнее подчеркивание
    slug = re.sub(r'[\s\-]+', '_', transliterated)
    
    # 3. Удаляем все символы, кроме букв, цифр и нижнего подчеркивания
    slug = re.sub(r'[^a-zA-Z0-9_]', '', slug)
    
    # 4. Приводим к нижнему регистру (по желанию) и убираем дубли подчёркиваний
    slug = re.sub(r'_+', '_', slug).strip('_').lower()
    
    return slug
