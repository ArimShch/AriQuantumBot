import re
import math

def format_gate_display(gate_name: str, controls: list, targets: list) -> str:
    """
    Форматирует гейт для отображения в таблице.
    Автоматически добавляет 'C' для управляющих кубитов и правильно расставляет аргументы.
    """
    # Разделяем имя гейта и параметр (если есть скобки, например Rx(π/2))
    match = re.match(r"^([a-zA-Z0-9]+)(?:\((.+)\))?$", gate_name)
    if match:
        base = match.group(1)
        param = match.group(2)
    else:
        base = gate_name
        param = None
        
    # Добавляем 'C' в зависимости от количества контролирующих кубитов
    prefix = "C" * len(controls)
    display_name = f"{prefix}{base}"
    
    # Формируем список аргументов
    args = []
    if param:
        args.append(param) # Параметр идет первым
    args.extend(map(str, controls))
    args.extend(map(str, targets))
    
    return f"{display_name}({', '.join(args)})"


def generate_gates_table_html(history: list, page: int, per_page: int = 10) -> str:
    """
    Генерирует HTML-таблицу с гейтами для текущей страницы.
    Заполнение идет сверху-вниз: левый столбец (1-6), правый столбец (7-12).
    """
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_gates = history[start_idx:end_idx]
    
    if not page_gates:
        return ""

    # Вычисляем количество строк (половина от количества гейтов на странице)
    half = math.ceil(len(page_gates) / 2)
    html = '<table>'
    
    for i in range(half):
        html += '<tr>'
        
        # Левая колонка
        left_idx = start_idx + i
        if left_idx < len(history):
            gate_str = format_gate_display(*history[left_idx])
            html += f'<td align="right">{left_idx + 1}</td><td align="left">{gate_str}</td>'
        else:
            html += '<td></td><td></td>'
            
        # Правая колонка
        right_idx = start_idx + half + i
        if right_idx < len(history) and right_idx < end_idx:
            gate_str = format_gate_display(*history[right_idx])
            html += f'<td align="right">{right_idx + 1}</td><td align="left">{gate_str}</td>'
        else:
            html += '<td></td><td></td>'
            
        html += '</tr>'
        
    html += '</table>'
    return html