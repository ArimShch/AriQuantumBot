# def draw_history(num_qubits: int, history: list) -> str:
#     lines = [f"q{i}: ─" for i in range(num_qubits)]
#     line_style = ['─'] * num_qubits  # '─' or '═'

#     for op in history:
#         name, ctrls, targets = op
#         target = targets[0]

#         # Шаг 1: выровнять все строки до текущей длины
#         # max_len = max(len(line) for line in lines)
#         # for i in range(num_qubits):
#         #     lines[i] += line_style[i] * (max_len - len(lines[i]))

#         if name == 'M':
#             lines[target] += 'M'
#             line_style[target] = '═'
#             lines[target] += '═'
#         else:
#             if ctrls:
#                 # Многоуправляющий гейт
#                 all_participants = sorted(ctrls + [target])
#                 min_q = all_participants[0]
#                 max_q = all_participants[-1]

#                 max_len = max(len(lines[number_line]) for number_line in range(min_q, max_q + 1))
#                 for i in range(min_q, max_q + 1):
#                     lines[i] += line_style[i] * (max_len - len(lines[i]))

#                 # На целевом кубите — имя гейта
#                 lines[target] += name

#                 # Обрабатываем каждый кубит в диапазоне [min_q, max_q]
#                 for q in range(min_q, max_q + 1):
#                     if q == target:
#                         continue  # уже обработан

#                     # Определяем символ
#                     if q in ctrls:
#                         # Это контролирующий кубит
#                         if min_q < q < max_q:
#                             # Внутренний контролирующий → ●
#                             sym = '●'
#                         else:
#                             # Крайний контролирующий
#                             if q < target:
#                                 sym = '┬'
#                             else:
#                                 sym = '┴'
#                     else:
#                         # Промежуточный кубит (не контроль, не цель)
#                         sym = '┼'

#                     # Учитываем стиль линии (после измерения)
#                     if line_style[q] == '═':
#                         # Заменяем символы на "двойные" версии
#                         sym_map = {'┬': '╦', '┴': '╩', '┼': '╬', '●': '●'}  # ● остаётся ●
#                         sym = sym_map.get(sym, sym)

#                     lines[q] += sym

#                 # Продолжаем линию после гейта
#                 for q in range(min_q, max_q + 1):
#                     lines[q] += line_style[q]
#             else:
#                 # Однокубитный гейт
#                 lines[target] += name + line_style[target]

#     # Финальное выравнивание
#     max_len = max(len(line) for line in lines)
#     result_lines = []
#     for i in range(num_qubits):
#         padded = lines[i] + line_style[i] * (max_len - len(lines[i])) + ' :'
#         # print(len(padded))
#         result_lines.append(padded)

#     return '\n'.join(result_lines)

def draw_history(num_qubits: int, history: list) -> str:
    lines = [f"q{i}: ─" for i in range(num_qubits)]
    line_style = ['─'] * num_qubits  # '─' or '═'

    for op in history:
        name, ctrls, targets = op
        target = targets[0]

        if name == 'M':
            lines[target] += 'M'
            line_style[target] = '═'
            lines[target] += '═'
        else:
            if ctrls:
                # Многоуправляющий гейт
                all_participants = sorted(ctrls + [target])
                min_q = all_participants[0]
                max_q = all_participants[-1]

                # Шаг 1: выровнять все строки в диапазоне участников
                max_len = max(len(lines[i]) for i in range(min_q, max_q + 1))
                for i in range(min_q, max_q + 1):
                    lines[i] += line_style[i] * (max_len - len(lines[i]))

                # Шаг 2: на целевом кубите добавить гейт
                lines[target] += name
                
                # Шаг 3: вычислить длину гейта и его центр
                gate_length = len(name)
                gate_center_offset = gate_length // 2  # смещение до центра
                # print(name, len(name), len(name) // 2)
                if gate_length % 2 == 0:
                    gate_center_offset -= 1
                
                # Шаг 4: для каждого кубита в диапазоне добавить символы
                for q in range(min_q, max_q + 1):
                    if q == target:
                        continue  # целевой кубит уже обработан

                    # Определяем символ
                    if q in ctrls:
                        # Это контролирующий кубит
                        if min_q < q < max_q:
                            sym = '●'
                        else:
                            sym = '┬' if q < target else '┴'
                    else:
                        sym = '┼'

                    # Учитываем стиль линии (после измерения)
                    if line_style[q] == '═':
                        sym_map = {'┬': '╦', '┴': '╩', '┼': '╬', '●': '●'}
                        sym = sym_map.get(sym, sym)

                    # Добавляем линию ДО центра гейта + символ + линию ПОСЛЕ
                    lines[q] += line_style[q] * gate_center_offset + sym + line_style[q] * (gate_length - gate_center_offset - 1)

                # Шаг 5: продолжаем линию после гейта
                for q in range(min_q, max_q + 1):
                    lines[q] += line_style[q]
            else:
                # Однокубитный гейт
                lines[target] += name + line_style[target]

    # Финальное выравнивание
    max_len = max(len(line) for line in lines)
    result_lines = []
    for i in range(num_qubits):
        padded = lines[i] + line_style[i] * (max_len - len(lines[i])) + ' :'
        result_lines.append(padded)

    return '\n'.join(result_lines)