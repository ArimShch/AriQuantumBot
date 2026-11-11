from aiogram.fsm.state import StatesGroup, State

class States(StatesGroup):
    menu = State()
    circuit_manage = State()
    
    input_theta_qubit = State()
    input_first_control_qubit = State()
    input_second_control_qubit = State()
    input_target_qubit = State()

    input_num_qubits = State()
    input_circuit_name = State()
    rename_circuit_name = State()

    choose_language = State()
    
    waiting_for_block_input = State()
    waiting_for_broadcast_ru = State()
    waiting_for_broadcast_en = State()
    waiting_for_user_search = State()