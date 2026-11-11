import logging
import re
import time
from typing import Optional, Dict, Any, Tuple, List
import numpy as np

from ariquantum import QuantumRegister
from qiskit import QuantumCircuit as QiskitCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


logger = logging.getLogger(__name__)

_ANGLE_RE = re.compile(r'^(\d*)π(?:/(\d+))?$')


def group_consecutive_measurements(history: list) -> list:
    """Группирует последовательные операции измерения в один вызов"""
    if not history:
        return []
    
    grouped = []
    i = 0
    
    while i < len(history):
        op = history[i]
        gate_name, controls, targets = op
        
        if gate_name == 'M':
            # Начинаем группировку измерений
            measurement_targets = []
            
            # Собираем все последовательные измерения
            while i < len(history) and history[i][0] == 'M':
                measurement_targets.extend(history[i][2])  # targets
                i += 1
            
            # Убираем дубликаты, сохраняя порядок
            unique_targets = []
            seen = set()
            for target in measurement_targets:
                if target not in seen:
                    unique_targets.append(target)
                    seen.add(target)
            
            grouped.append(['M_GROUP', [], unique_targets])
        else:
            grouped.append(op)
            i += 1
    
    return grouped


def parse_angle(params: str) -> float:
    """Разбирает угол: число (радианы) или запись вида π, π/2, 3π/4, 2π."""
    params = params.strip()
    match = _ANGLE_RE.match(params)
    if match:
        numerator = int(match.group(1)) if match.group(1) else 1
        denominator = int(match.group(2)) if match.group(2) else 1
        return numerator * np.pi / denominator
    return float(params)


def split_gate_name(gate_name: str) -> Tuple[str, float]:
    """Разделяет 'Rx(π/2)' на ('Rx', π/2). Для гейтов без параметра угол = 1."""
    if '(' not in gate_name:
        return gate_name, 1
    base_name, params = gate_name.split('(', 1)
    params = params.rstrip(')')
    if not params:
        raise ValueError(f'Gate {gate_name!r} has an empty angle')
    return base_name, parse_angle(params)


def apply_gate_to_ariquantum(qr: QuantumRegister, op: list) -> None:
    """Применяет операцию к AriQuantum регистру"""
    gate_name, controls, targets = op
    target = targets[0] if targets else None
    base_name, angle = split_gate_name(gate_name)
    n_ctrl = len(controls)

    if base_name == 'M_GROUP':
        # Для AriQuantum измерения группируются автоматически
        qr.measure(targets)
        return

    # Гейты без параметра: (имя, число контролей) -> метод регистра
    plain = {
        ('I', 0): qr.i, ('X', 0): qr.x, ('Y', 0): qr.y, ('Z', 0): qr.z,
        ('H', 0): qr.h, ('S', 0): qr.s, ('T', 0): qr.t,
    }
    # Параметрические гейты: сигнатура (qubit, theta)
    param = {
        ('P', 0): qr.p, ('Rx', 0): qr.rx, ('Ry', 0): qr.ry, ('Rz', 0): qr.rz,
    }
    controlled = {
        ('X', 1): qr.cx, ('Y', 1): qr.cy, ('Z', 1): qr.cz,
        ('H', 1): qr.ch, ('S', 1): qr.cs,
    }
    controlled_param = {
        ('P', 1): qr.cp, ('Rx', 1): qr.crx, ('Ry', 1): qr.cry, ('Rz', 1): qr.crz,
    }
    toffoli = {('X', 2): qr.ccx, ('Z', 2): qr.ccz}

    key = (base_name, n_ctrl)
    if key in plain:
        plain[key](target)
    elif key in param:
        param[key](target, angle)
    elif key in controlled:
        controlled[key](controls[0], target)
    elif key in controlled_param:
        controlled_param[key](controls[0], target, angle)
    elif key in toffoli:
        toffoli[key](controls[0], controls[1], target)
    else:
        raise ValueError(f'Unsupported gate {gate_name!r} with {n_ctrl} controls')


def apply_gate_to_qiskit(qc: QiskitCircuit, op: list, num_qubits: int) -> None:
    """Применяет операцию к Qiskit схеме"""
    gate_name, controls, targets = op
    target = targets[0] if targets else None
    base_name, angle = split_gate_name(gate_name)
    n_ctrl = len(controls)

    if base_name == 'M_GROUP':
        qc.measure(targets, targets)
        return

    plain = {
        ('I', 0): qc.id, ('X', 0): qc.x, ('Y', 0): qc.y, ('Z', 0): qc.z,
        ('H', 0): qc.h, ('S', 0): qc.s, ('T', 0): qc.t,
    }
    # Параметрические гейты Qiskit: сигнатура (theta, qubit)
    param = {
        ('P', 0): qc.p, ('Rx', 0): qc.rx, ('Ry', 0): qc.ry, ('Rz', 0): qc.rz,
    }
    controlled = {
        ('X', 1): qc.cx, ('Y', 1): qc.cy, ('Z', 1): qc.cz,
        ('H', 1): qc.ch, ('S', 1): qc.cs,
    }
    controlled_param = {
        ('P', 1): qc.cp, ('Rx', 1): qc.crx, ('Ry', 1): qc.cry, ('Rz', 1): qc.crz,
    }
    toffoli = {('X', 2): qc.ccx, ('Z', 2): qc.ccz}

    key = (base_name, n_ctrl)
    if key in plain:
        plain[key](target)
    elif key in param:
        param[key](angle, target)
    elif key in controlled:
        controlled[key](controls[0], target)
    elif key in controlled_param:
        controlled_param[key](angle, controls[0], target)
    elif key in toffoli:
        toffoli[key](controls[0], controls[1], target)
    else:
        raise ValueError(f'Unsupported gate {gate_name!r} with {n_ctrl} controls')


def simulate_circuit(
    history: list,
    num_qubits: int,
    backend_name: str,
    shots: int = 10
) -> Tuple[str, Optional[Dict[str, int]], float]:
    """
    Выполняет симуляцию квантовой схемы.
    
    Returns:
        Tuple[braket_state: str, counts: Optional[Dict], execution_time: float]
    """
    start_time = time.perf_counter()
    
    # Группируем последовательные измерения
    grouped_history = group_consecutive_measurements(history)
    
    has_measurements = any(op[0] in ['M', 'M_GROUP'] for op in grouped_history)
    
    if backend_name == 'AriQuantum':
        # Симуляция с AriQuantum
        qr = QuantumRegister(num_qubits, "0")
        
        # Применяем все операции до первого измерения для вектора состояния
        state_before_measurement = None
        found_measurement = False
        
        for op in grouped_history:
            if op[0] in ['M', 'M_GROUP'] and not found_measurement:
                # Сохраняем состояние до первого измерения
                state_before_measurement = str(qr)
                found_measurement = True
            
            apply_gate_to_ariquantum(qr, op)
        
        if state_before_measurement is None:
            # Нет измерений - используем конечное состояние
            braket_state = str(qr)
            counts = None
        else:
            braket_state = state_before_measurement
            # Получаем статистику измерений
            if has_measurements:
                try:
                    counts_dict = qr.get_counts(shots)
                    # Конвертируем ключи в строки если нужно
                    counts = {str(k): v for k, v in counts_dict.items()}
                except Exception:
                    logger.exception('AriQuantum get_counts failed')
                    counts = None
            else:
                counts = None
    
    else:  # qiskit
        # Симуляция с Qiskit
        qc = QiskitCircuit(num_qubits, num_qubits if has_measurements else 0)
        
        # Применяем все операции до первого измерения для вектора состояния
        state_before_measurement = None
        found_measurement = False
        
        for op in grouped_history:
            if op[0] in ['M', 'M_GROUP'] and not found_measurement:
                # Для Qiskit получаем состояние через Statevector
                state_before_measurement = Statevector(qc).to_dict()
                found_measurement = True
            
            apply_gate_to_qiskit(qc, op, num_qubits)
        
        if state_before_measurement is None:
            # Нет измерений
            final_state = Statevector(qc)
            # Конвертируем в строку в нотации Дирака
            braket_state = _statevector_to_braket(final_state, num_qubits)
            counts = None
        else:
            braket_state = _statevector_to_braket(state_before_measurement, num_qubits)
            if has_measurements:
                # Запускаем симуляцию с измерениями
                simulator = AerSimulator()
                compiled_circuit = transpile(qc, simulator)
                result = simulator.run(compiled_circuit, shots=shots).result()
                counts = result.get_counts()
                counts = {k[::-1]: v for k, v in counts.items()}
            else:
                counts = None
    
    execution_time = time.perf_counter() - start_time
    return braket_state, counts, execution_time


def _statevector_to_braket(statevector, num_qubits: int = 0, decimals: int = 4) -> str:
    """Конвертирует Statevector или словарь {базис: амплитуда} в строку Дирака"""
    if isinstance(statevector, Statevector):
        state_dict = statevector.to_dict()
    else:
        state_dict = statevector

    terms = []
    for basis, amplitude in state_dict.items():
        if abs(amplitude) > 1e-10:
            real = round(amplitude.real, decimals)
            imag = round(amplitude.imag, decimals)

            if imag == 0:
                coeff = f"{real:.{decimals}f}"
            elif real == 0:
                coeff = f"{imag:.{decimals}f}j"
            else:
                coeff = f"({real:.{decimals}f}{imag:+.{decimals}f}j)"

            terms.append(f"{coeff}|{basis[::-1]}⟩")

    if not terms:
        return "0"
    return " + ".join(terms)
