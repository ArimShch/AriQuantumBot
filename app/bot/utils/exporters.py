import numpy as np
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.qasm3 import dumps as qasm3_dumps
from qiskit.qasm2 import dumps as qasm2_dumps


# ============================================================
# Вспомогательные функции
# ============================================================

def group_consecutive_measurements(history: list) -> list:
    """Группирует последовательные операции M в один вызов (не меняет БД)"""
    if not history:
        return []

    grouped = []
    i = 0
    while i < len(history):
        op = history[i]
        gate_name, controls, targets = op

        if gate_name == 'M':
            measurement_targets = []
            while i < len(history) and history[i][0] == 'M':
                measurement_targets.extend(history[i][2])
                i += 1
            # Убираем дубликаты, сохраняя порядок
            unique_targets = []
            seen = set()
            for t in measurement_targets:
                if t not in seen:
                    unique_targets.append(t)
                    seen.add(t)
            grouped.append(['M', [], unique_targets])
        else:
            grouped.append(op)
            i += 1

    return grouped


def _parse_gate(op: list):
    """Разбирает операцию на base_name, angle_str, controls, targets"""
    gate_name, controls, targets = op
    target = targets[0] if targets else None

    if '(' in gate_name:
        base_name, params = gate_name.split('(', 1)
        angle_str = params.rstrip(')')
    else:
        base_name = gate_name
        angle_str = None

    return base_name, angle_str, controls, targets, target


def _angle_to_numpy_code(angle_str: str) -> str:
    """Конвертирует строку угла в Python-код с numpy"""
    if not angle_str:
        return 'np.pi'

    mapping = {
        'π/6':   'np.pi/6',
        'π/4':   'np.pi/4',
        'π/3':   'np.pi/3',
        'π/2':   'np.pi/2',
        '2π/3':  '2*np.pi/3',
        '3π/4':  '3*np.pi/4',
        '5π/6':  '5*np.pi/6',
        'π':     'np.pi',
        '7π/6':  '7*np.pi/6',
        '3π/2':  '3*np.pi/2',
        '2π':    '2*np.pi',
    }
    return mapping.get(angle_str, angle_str)


def _angle_to_float(angle_str: str) -> float:
    """Конвертирует строку угла в числовое значение (для Qiskit API)"""
    if not angle_str:
        return np.pi

    mapping = {
        'π/6':   np.pi / 6,
        'π/4':   np.pi / 4,
        'π/3':   np.pi / 3,
        'π/2':   np.pi / 2,
        '2π/3':  2 * np.pi / 3,
        '3π/4':  3 * np.pi / 4,
        '5π/6':  5 * np.pi / 6,
        'π':     np.pi,
        '7π/6':  7 * np.pi / 6,
        '3π/2':  3 * np.pi / 2,
        '2π':    2 * np.pi,
    }
    return mapping.get(angle_str)


def _has_parametric_gates(grouped_history: list) -> bool:
    """Проверяет, есть ли в истории параметрические гейты"""
    for op in grouped_history:
        if op[0] == 'M':
            continue
        if '(' in op[0]:
            return True
    return False


# ============================================================
# Экспорт в AriQuantum Python-код
# ============================================================

def export_to_ariquantum(circuit, shots: int = 100) -> str:
    grouped = group_consecutive_measurements(circuit.circuit_history)
    has_measurements = any(op[0] == 'M' for op in grouped)
    needs_numpy = _has_parametric_gates(grouped)

    lines = []

    # Импорты
    if needs_numpy:
        lines.append('import numpy as np')
    lines.append('from ariquantum import QuantumRegister')
    lines.append('')
    lines.append(f'qr = QuantumRegister({circuit.num_qubits})')
    lines.append('')

    # Гейты
    for op in grouped:
        base_name, angle_str, controls, targets, target = _parse_gate(op)

        if base_name == 'M':
            targets_str = ', '.join(map(str, targets))
            lines.append(f'qr.measure([{targets_str}])')

        elif len(controls) == 0:
            if base_name in ('I', 'X', 'Y', 'Z', 'H', 'S', 'T'):
                lines.append(f'qr.{base_name.lower()}({target})')
            elif base_name in ('P', 'Rx', 'Ry', 'Rz'):
                angle_code = _angle_to_numpy_code(angle_str)
                lines.append(f'qr.{base_name.lower()}({target}, {angle_code})')

        elif len(controls) == 1:
            if base_name in ('X', 'Y', 'Z', 'H', 'S'):
                lines.append(f'qr.c{base_name.lower()}({controls[0]}, {target})')
            elif base_name in ('P', 'Rx', 'Ry', 'Rz'):
                angle_code = _angle_to_numpy_code(angle_str)
                short = base_name[1:].lower()  # Rx -> x, Ry -> y, Rz -> z, P -> p
                if base_name == 'P':
                    short = 'p'
                lines.append(f'qr.cr{short}({controls[0]}, {target}, {angle_code})')

        elif len(controls) == 2:
            if base_name == 'X':
                lines.append(f'qr.ccx({controls[0]}, {controls[1]}, {target})')
            elif base_name == 'Z':
                lines.append(f'qr.ccz({controls[0]}, {controls[1]}, {target})')

    # Финальный блок
    lines.append('')
    lines.append('state = qr.as_bracket_string()')
    if has_measurements:
        lines.append(f'counts = qr.get_counts(shots={shots})')
    lines.append('')
    lines.append('qr.draw_circuit()')
    lines.append('')
    lines.append("print('State vector:\\n', state)")
    if has_measurements:
        lines.append("print('Counts:\\n', counts)")

    return '\n'.join(lines)


# ============================================================
# Экспорт в Qiskit Python-код
# ============================================================

def export_to_qiskit(circuit, shots: int = 100) -> str:
    grouped = group_consecutive_measurements(circuit.circuit_history)
    has_measurements = any(op[0] == 'M' for op in grouped)
    needs_numpy = _has_parametric_gates(grouped)

    lines = []

    # Импорты
    if needs_numpy:
        lines.append('import numpy as np')
    lines.append('from qiskit import QuantumCircuit')

    if has_measurements:
        lines.append('from qiskit import transpile')
        lines.append('from qiskit_aer import AerSimulator')
    else:
        lines.append('from qiskit.quantum_info import Statevector')

    lines.append('')

    # Создание схемы
    if has_measurements:
        lines.append(f'qc = QuantumCircuit({circuit.num_qubits}, {circuit.num_qubits})')
    else:
        lines.append(f'qc = QuantumCircuit({circuit.num_qubits})')
    lines.append('')

    # Гейты
    for op in grouped:
        base_name, angle_str, controls, targets, target = _parse_gate(op)

        if base_name == 'M':
            targets_str = ', '.join(map(str, targets))
            lines.append(f'qc.measure([{targets_str}], [{targets_str}])')

        elif len(controls) == 0:
            if base_name in ('I', 'X', 'Y', 'Z', 'H', 'S', 'T'):
                lines.append(f'qc.{base_name.lower()}({target})')
            elif base_name in ('P', 'Rx', 'Ry', 'Rz'):
                angle_code = _angle_to_numpy_code(angle_str)
                lines.append(f'qc.{base_name.lower()}({angle_code}, {target})')

        elif len(controls) == 1:
            if base_name in ('X', 'Y', 'Z', 'H', 'S'):
                lines.append(f'qc.c{base_name.lower()}({controls[0]}, {target})')
            elif base_name in ('P', 'Rx', 'Ry', 'Rz'):
                angle_code = _angle_to_numpy_code(angle_str)
                short = base_name[1:].lower()
                if base_name == 'P':
                    short = 'p'
                lines.append(f'qc.cr{short}({angle_code}, {controls[0]}, {target})')

        elif len(controls) == 2:
            if base_name == 'X':
                lines.append(f'qc.ccx({controls[0]}, {controls[1]}, {target})')
            elif base_name == 'Z':
                lines.append(f'qc.ccz({controls[0]}, {controls[1]}, {target})')

    # Финальный блок
    lines.append('')
    if has_measurements:
        lines.append('simulator = AerSimulator()')
        lines.append('compiled = transpile(qc, simulator)')
        lines.append(f'result = simulator.run(compiled, shots={shots}).result()')
        lines.append('counts = result.get_counts()')
        lines.append('')
        lines.append("print(qc.draw(output='text'))")
        lines.append("print('Counts:\\n', counts)")
    else:
        lines.append('state = Statevector(qc)')
        lines.append('')
        lines.append("print(qc.draw(output='text'))")
        lines.append("print('State vector:\\n', state)")

    return '\n'.join(lines)


# ============================================================
# Вспомогательная: построение Qiskit Circuit (для QASM)
# ============================================================

def _build_qiskit_circuit(circuit) -> QiskitCircuit:
    """Строит Qiskit-схему из истории (для дампа в QASM)"""
    grouped = group_consecutive_measurements(circuit.circuit_history)
    has_measurements = any(op[0] == 'M' for op in grouped)

    if has_measurements:
        qc = QiskitCircuit(circuit.num_qubits, circuit.num_qubits)
    else:
        qc = QiskitCircuit(circuit.num_qubits)

    for op in grouped:
        base_name, angle_str, controls, targets, target = _parse_gate(op)
        angle = _angle_to_float(angle_str) if angle_str else None

        if base_name == 'M':
            qc.measure(targets, targets)

        elif len(controls) == 0:
            if base_name == 'I':     qc.i(target)
            elif base_name == 'X':   qc.x(target)
            elif base_name == 'Y':   qc.y(target)
            elif base_name == 'Z':   qc.z(target)
            elif base_name == 'H':   qc.h(target)
            elif base_name == 'S':   qc.s(target)
            elif base_name == 'T':   qc.t(target)
            elif base_name == 'P':   qc.p(angle, target)
            elif base_name == 'Rx':  qc.rx(angle, target)
            elif base_name == 'Ry':  qc.ry(angle, target)
            elif base_name == 'Rz':  qc.rz(angle, target)

        elif len(controls) == 1:
            if base_name == 'X':   qc.cx(controls[0], target)
            elif base_name == 'Y': qc.cy(controls[0], target)
            elif base_name == 'Z': qc.cz(controls[0], target)
            elif base_name == 'H': qc.ch(controls[0], target)
            elif base_name == 'S': qc.cs(controls[0], target)
            elif base_name == 'P':   qc.cp(angle, controls[0], target)
            elif base_name == 'Rx':  qc.crx(angle, controls[0], target)
            elif base_name == 'Ry':  qc.cry(angle, controls[0], target)
            elif base_name == 'Rz':  qc.crz(angle, controls[0], target)

        elif len(controls) == 2:
            if base_name == 'X': qc.ccx(controls[0], controls[1], target)
            elif base_name == 'Z': qc.ccz(controls[0], controls[1], target)

    return qc


def export_to_qasm2(circuit) -> str:
    """Экспортирует схему в OpenQASM 2.0"""
    qc = _build_qiskit_circuit(circuit)
    return qasm2_dumps(qc)


def export_to_qasm3(circuit) -> str:
    """Экспортирует схему в OpenQASM 3.0"""
    qc = _build_qiskit_circuit(circuit)
    return qasm3_dumps(qc)