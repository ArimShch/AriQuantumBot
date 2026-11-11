from qiskit import QuantumCircuit
from qiskit import transpile
from qiskit_aer import AerSimulator

qc = QuantumCircuit(8, 8)

qc.h(0)
qc.ccx(0, 1, 2)
qc.h(1)
qc.ccx(1, 2, 3)
qc.h(2)
qc.ccx(2, 3, 4)
qc.h(3)
qc.ccx(3, 4, 5)
qc.h(4)
qc.ccx(4, 5, 6)
qc.h(5)
qc.ccx(5, 6, 7)
qc.measure([0, 1, 2, 3, 4, 5, 6, 7], [0, 1, 2, 3, 4, 5, 6, 7])

simulator = AerSimulator()
compiled = transpile(qc, simulator)
result = simulator.run(compiled, shots=1000).result()
counts = result.get_counts()

print(qc.draw(output='text'))
print('Counts:\n', counts)
