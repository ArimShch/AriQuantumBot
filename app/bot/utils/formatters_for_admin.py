from html import escape

def format_user_link(user_tuple: tuple) -> str:
    """
    Форматирует пользователя для отображения в статистике
    
    Args:
        user_tuple: (user_id, username, first_name, last_name)
    
    Returns:
        HTML строку с отформатированным именем и ссылкой
    """
    user_id, username, first_name, last_name = user_tuple[0], user_tuple[1], user_tuple[2], user_tuple[3]
    
    # Очищаем имя и фамилию от пробелов
    first_name_clean = (first_name or '').strip()
    last_name_clean = (last_name or '').strip()
    
    # Определяем отображаемое имя
    if first_name_clean and last_name_clean:
        display_name = f"{first_name_clean} {last_name_clean}"
    elif first_name_clean:
        display_name = first_name_clean
    elif last_name_clean:
        display_name = last_name_clean
    else:
        # Если оба пустые, показываем ID в формате id12372438793
        display_name = f"id{user_id}"
    
    # Экранируем HTML символы для безопасности
    display_name = escape(display_name)
    
    # Формируем ссылку
    if username:
        # Если есть username, делаем кликабельную ссылку
        return f"<a href='https://t.me/{username}'>{display_name}</a>"
    else:
        # Если нет username, показываем без ссылки
        return f"<a href='tg://user?id={user_id}'>{display_name}</a>"