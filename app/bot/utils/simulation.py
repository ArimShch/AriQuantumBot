import time
from typing import Optional, Dict, Any, Tuple, List
import numpy as np

from ariquantum import QuantumRegister
from qiskit import QuantumCircuit as QiskitCircuit, transpile
from qiskit_aer import AerSimulator


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


def apply_gate_to_ariquantum(qr: QuantumRegister, op: list) -> None:
    """Применяет операцию к AriQuantum регистру"""
    gate_name, controls, targets = op
    target = targets[0] if targets else None


    # Обработка параметрических гейтов
    if '(' in gate_name:
        base_name, params = gate_name.split('(', 1)
        params = params.rstrip(')')
        if params:
            # Обработка углов вроде π/2, π/4
            if params == 'π/6':
                angle = np.pi / 6
            elif params == 'π/4':
                angle = np.pi / 4
            elif params == 'π/3':
                angle = np.pi / 3
            elif params == 'π/2':
                angle = np.pi / 2
            elif params == '2π/3':
                angle = 2 * np.pi / 3
            elif params == '3π/4':
                angle = 3 * np.pi / 4
            elif params == '5π/6':
                angle = 5 * np.pi / 6
            elif params == 'π':
                angle = np.pi
            elif params == '7π/6':
                angle = 7 * np.pi / 6
            elif params == '3π/2':
                angle = 3 * np.pi / 2
            elif params == '2π':
                angle = 2 * np.pi
            else:
                angle = float(params)
        else:
            angle = float(params)
    else:
        base_name = gate_name
        angle = 1
    
    # Применение гейтов
    if base_name == 'I' and len(controls) == 0:
        qr.i(target)
    elif base_name == 'X' and len(controls) == 0:
        qr.x(target)
    elif base_name == 'Y' and len(controls) == 0:
        qr.y(target)
    elif base_name == 'Z' and len(controls) == 0:
        qr.z(target)
    elif base_name == 'H' and len(controls) == 0:
        qr.h(target)
    elif base_name == 'S' and len(controls) == 0:
        qr.s(target)
    elif base_name == 'T' and len(controls) == 0:
        qr.t(target)
    elif base_name == 'P' and len(controls) == 0:
        qr.p(target, angle)
    elif base_name == 'Rx' and len(controls) == 0:
        qr.rx(target, angle)
    elif base_name == 'Ry' and len(controls) == 0:
        qr.ry(target, angle)
    elif base_name == 'Rz' and len(controls) == 0:
        qr.rz(target, angle)
    elif base_name == 'X' and len(controls) == 1:
        qr.cx(controls[0], target)
    elif base_name == 'Y' and len(controls) == 1:
        qr.cy(controls[0], target)
    elif base_name == 'Z' and len(controls) == 1:
        qr.cz(controls[0], target)
    elif base_name == 'H' and len(controls) == 1:
        qr.ch(controls[0], target)
    elif base_name == 'S' and len(controls) == 1:
        qr.cs(controls[0], target)
    elif base_name == 'P' and len(controls) == 1:
        qr.cp(controls[0], target, angle)
    elif base_name == 'Rx' and len(controls) == 1:
        qr.crx(controls[0], target, angle)
    elif base_name == 'Ry' and len(controls) == 1:
        qr.cry(controls[0], target, angle)
    elif base_name == 'Rz' and len(controls) == 1:
        qr.crz(controls[0], target, angle)
    elif base_name == 'X' and len(controls) == 2:
        qr.ccx(controls[0], controls[1], target, angle)
    elif base_name == 'Z' and len(controls) == 2:
        qr.ccz(controls[0], controls[1], target, angle)
    elif base_name == 'M_GROUP':
        # Для AriQuantum измерения группируются автоматически
        qr.measure(targets)



def apply_gate_to_qiskit(qc: QiskitCircuit, op: list, num_qubits: int) -> None:
    """Применяет операцию к Qiskit схеме"""
    gate_name, controls, targets = op
    target = targets[0] if targets else None
    
    # Обработка параметрических гейтов
    if '(' in gate_name:
        base_name, params = gate_name.split('(', 1)
        params = params.rstrip(')')
        if params:
            if params == 'π/6':
                angle = np.pi / 6
            elif params == 'π/4':
                angle = np.pi / 4
            elif params == 'π/3':
                angle = np.pi / 3
            elif params == 'π/2':
                angle = np.pi / 2
            elif params == '2π/3':
                angle = 2 * np.pi / 3
            elif params == '3π/4':
                angle = 3 * np.pi / 4
            elif params == '5π/6':
                angle = 5 * np.pi / 6
            elif params == 'π':
                angle = np.pi
            elif params == '7π/6':
                angle = 7 * np.pi / 6
            elif params == '3π/2':
                angle = 3 * np.pi / 2
            elif params == '2π':
                angle = 2 * np.pi
            else:
                angle = float(params)
        else:
            angle = float(params)
    else:
        base_name = gate_name
        angle = 1
    
    # Применение гейтов
    if base_name == 'I' and len(controls) == 0:
        qc.i(target)
    elif base_name == 'X' and len(controls) == 0:
        qc.x(target)
    elif base_name == 'Y' and len(controls) == 0:
        qc.y(target)
    elif base_name == 'Z' and len(controls) == 0:
        qc.z(target)
    elif base_name == 'H' and len(controls) == 0:
        qc.h(target)
    elif base_name == 'S' and len(controls) == 0:
        qc.s(target)
    elif base_name == 'T' and len(controls) == 0:
        qc.t(target)
    elif base_name == 'P' and len(controls) == 0:
        qc.p(angle, target)
    elif base_name == 'Rx' and len(controls) == 0:
        qc.rx(angle, target)
    elif base_name == 'Ry' and len(controls) == 0:
        qc.ry(angle, target)
    elif base_name == 'Rz' and len(controls) == 0:
        qc.rz(angle, target)
    elif base_name == 'X' and len(controls) == 1:
        qc.cx(controls[0], target)
    elif base_name == 'Y' and len(controls) == 1:
        qc.cy(controls[0], target)
    elif base_name == 'Z' and len(controls) == 1:
        qc.cz(controls[0], target)
    elif base_name == 'H' and len(controls) == 1:
        qc.ch(controls[0], target)
    elif base_name == 'S' and len(controls) == 1:
        qc.cs(controls[0], target)
    elif base_name == 'P' and len(controls) == 1:
        qc.cp(angle, controls[0], target)
    elif base_name == 'Rx' and len(controls) == 1:
        qc.crx(angle, controls[0], target)
    elif base_name == 'Ry' and len(controls) == 1:
        qc.cry(angle, controls[0], target)
    elif base_name == 'Rz' and len(controls) == 1:
        qc.crz(angle, controls[0], target)
    elif base_name == 'X' and len(controls) == 2:
        qc.ccx(controls[0], controls[1], target)
    elif base_name == 'Z' and len(controls) == 2:
        qc.ccz(controls[0], controls[1], target)
    elif base_name == 'M_GROUP':
        # # Измеряем в правильном порядке (обратный для Qiskit)
        # if len(targets) > 1:
        #     # Создаем классический регистр той же длины
        #     creg_size = len(targets)
        #     # Измеряем в обратном порядке
        #     reversed_targets = list(reversed(targets))
        #     print(reversed_targets)
        #     for i, qubit in enumerate(reversed_targets):
        #         print(qubit, i)
        #         qc.measure(qubit, i)
        # else:
        #     qc.measure(targets[0], 0)
        qc.measure(targets, targets)


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
                except:
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
                from qiskit.quantum_info import Statevector
                state_before_measurement = Statevector(qc).to_dict()
                found_measurement = True
            
            apply_gate_to_qiskit(qc, op, num_qubits)
        
        if state_before_measurement is None:
            # Нет измерений
            from qiskit.quantum_info import Statevector
            final_state = Statevector(qc)
            # Конвертируем в строку в нотации Дирака
            braket_state = _statevector_to_braket(final_state, num_qubits)
            counts = None
        else:
            braket_state = _statevector_to_braket_dict(state_before_measurement, num_qubits)
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


def _statevector_to_braket(statevector, num_qubits: int, decimals: int = 4) -> str:
    """Конвертирует Statevector в строку Дирака"""
    from qiskit.quantum_info import Statevector
    if isinstance(statevector, Statevector):
        state_dict = statevector.to_dict()
    else:
        state_dict = statevector
    
    terms = []
    for basis, amplitude in state_dict.items():
        if abs(amplitude) > 1e-10:
            # Форматируем амплитуду
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


def _statevector_to_braket_dict(state_dict: dict, num_qubits: int, decimals: int = 4) -> str:
    """Конвертирует словарь состояния в строку Дирака"""
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