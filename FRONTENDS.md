# Supported Quantum Frontends

This document lists all the quantum programming frameworks (frontends) that are supported by Orquestra QRE. A frontend refers to any programming language or framework you can use to write quantum circuits that can be analyzed, optimized, and executed through Orquestra QRE.

## Currently Supported Frontends

| Frontend | Integration Status | Notes |
|----------|-------------------|-------|
| Qiskit | ✅ Full support | IBM's quantum computing framework |
| Cirq | ✅ Full support | Google's quantum computing framework |
| PyQuil | ✅ Full support | Rigetti's quantum computing framework |
| PennyLane | ⚠️ Experimental | Only basic circuit conversion supported |
| Braket | ⚠️ Experimental | Amazon's quantum computing service |

## Installation

To install Orquestra QRE with support for specific frontends:

```bash
# Install with Qiskit support
pip install orquestra-qre[qiskit]

# Install with Cirq support
pip install orquestra-qre[cirq]

# Install with multiple frontend support
pip install orquestra-qre[qiskit,cirq,pyquil]

# Install with all frontends
pip install orquestra-qre[all]
```

## Frontend Conversion

Orquestra QRE can convert quantum circuits between different frontends. For example:

```python
from orquestra_qre.core import convert_circuit

# Convert from Qiskit to Cirq
cirq_circuit = convert_circuit(qiskit_circuit, "cirq") 

# Convert from Cirq to PyQuil
pyquil_circuit = convert_circuit(cirq_circuit, "pyquil")
```

## Backend Compatibility

Each supported frontend can connect to its corresponding backend providers:

| Frontend | Compatible Backends |
|----------|-------------------|
| Qiskit | IBM Quantum Experience, AerSimulator |
| Cirq | Google Quantum AI, Cirq Simulator |
| PyQuil | Rigetti QCS, QVM |
| PennyLane | Lightning Simulator, other PennyLane devices |
| Braket | AWS Braket managed backends (IonQ, Rigetti, etc.) |

## Adding New Frontend Support

Orquestra QRE is designed to be extensible. To add support for a new frontend:

1. Create a new module in `orquestra_qre` that handles conversion to/from the frontend
2. Implement the required interface functions (circuit conversion, execution, etc.)
3. Update the conversion registry in `orquestra_qre/core.py`
4. Add test cases for the new frontend
5. Update this document to include the new frontend

For more information on implementing new frontends, see the [development guide](./CONTRIBUTING.md).
