TEMPLATES = {
    "bell": {
        "name_ru": "Состояние Белла",
        "name_en": "Bell State",
        "num_qubits": 2,
        "desc_ru": "Базовый пример квантовой запутанности. Создает максимально запутанное состояние, при котором измерение одного кубита мгновенно определяет состояние второго.",
        "desc_en": "A basic example of quantum entanglement. Creates a maximally entangled state where measuring one qubit instantly determines the state of the other.",
        "history": [["H", [], [0]], ["X", [0], [1]]],
    },
    "ghz": {
        "name_ru": "Состояние GHZ",
        "name_en": "GHZ State",
        "num_qubits": 3,
        "desc_ru": "Состояние Гринбергера — Хорна — Цайлингера. Демонстрирует многочастичную квантовую запутанность для трёх кубитов.",
        "desc_en": "Greenberger–Horne–Zeilinger state. Demonstrates multi-particle quantum entanglement for three qubits.",
        "history": [["H", [], [0]], ["X", [0], [1]], ["X", [1], [2]]],
    },
    "superdense": {
        "name_ru": "Сверхплотное кодирование",
        "name_en": "Superdense Coding",
        "num_qubits": 2,
        "desc_ru": "Протокол, позволяющий Алисе передать Бобу два классических бита информации (в данном случае '11'), отправив всего один квантовый бит, используя заранее подготовленную запутанность.",
        "desc_en": "A protocol allowing Alice to send Bob two classical bits of info (here '11') by transmitting just one qubit, using pre-shared entanglement.",
        "history": [
            ["H", [], [0]], ["X", [0], [1]],  # Создание пары Белла
            ["X", [], [0]], ["Z", [], [0]],    # Кодирование '11' Алисой
            ["X", [0], [1]], ["H", [], [0]]   # Декодирование Бобом
        ],
    },
    "teleportation": {
        "name_ru": "Квантовая телепортация",
        "name_en": "Quantum Teleportation",
        "num_qubits": 3,
        "desc_ru": "Передача произвольного квантового состояния (на q0) от Алисы к Бобу (на q2) с использованием запутанности и классических каналов связи (отложенное измерение).",
        "desc_en": "Transfer of an arbitrary quantum state (on q0) from Alice to Bob (on q2) using entanglement and classical communication (deferred measurement).",
        "history": [
            ["H", [], [1]], ["X", [1], [2]],  # Запутанность Алисы и Боба
            ["X", [0], [1]], ["H", [], [0]],  # Операции Алисы
            ["X", [1], [2]], ["Z", [0], [2]] # Корректирующие гейты Боба
        ],
    },
    "chsh": {
        "name_ru": "Тест неравенства Белла / CHSH",
        "name_en": "Bell Inequality Test / CHSH",
        "num_qubits": 2,
        "desc_ru": "Базовая схема для проверки нарушений неравенств Белла. Использует повороты Ry для изменения базиса измерения Алисы и Боба.",
        "desc_en": "A base circuit for testing Bell inequality violations. Uses Ry rotations to change the measurement basis for Alice and Bob.",
        "history": [
            ["H", [], [0]], ["X", [0], [1]],  # Пара Белла
            ["Ry(π/4)", [], [0]], ["Ry(-π/8)", [], [1]] # Смена базисов
        ],
    }
}