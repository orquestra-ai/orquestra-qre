# Supported Quantum Frontends & Platform Interfaces

This document lists all the quantum programming frameworks (frontends) and platform interfaces that are supported by Orquestra QRE. A frontend refers to any programming language or framework you can use to write quantum circuits, while platform interfaces provide different ways to access and interact with the quantum resource estimation capabilities.

## Platform Interfaces

| Interface | Status | Description | Launch Command |
|-----------|--------|-------------|----------------|
| **🖥️ Desktop App (Tauri)** | ✅ **Fully Operational** | Native cross-platform desktop application | `npm run tauri:dev` |
| **📊 Streamlit Dashboard** | ✅ Fully Operational | Interactive web dashboard with visualizations | `streamlit run streamlit_app.py` |
| **📓 Jupyter Notebooks** | ✅ Fully Operational | Research environment for analysis | `jupyter notebook` |
| **⌨️ CLI Interface** | ✅ Fully Operational | Command-line tools for automation | `python -m orquestra_qre.cli` |
| **🐍 Python SDK** | ✅ Fully Operational | Programmatic API access | `from orquestra_qre import *` |
| **🌐 Web Interface** | ✅ Fully Operational | React/TypeScript frontend | `python simple_run.py` |

## Quantum Programming Frontends

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

## Desktop Application Usage

The **Tauri desktop application** provides a native, cross-platform interface for quantum resource estimation. 

### Features
- **Complete QuantumOrchestra Interface**: Full access to all quantum resource estimation features
- **Native Performance**: Optimized desktop performance with Rust backend
- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Offline Capable**: Works without internet connection for local calculations
- **File System Integration**: Save and load quantum circuits and results

### Getting Started with Desktop App

```bash
# Prerequisites: Node.js, npm, and Rust
# Install dependencies
npm install

# Run in development mode
npm run tauri:dev

# Build for production
npm run tauri:build
```

### Desktop App vs Web Interface

| Feature | Desktop App | Web Interface |
|---------|------------|---------------|
| **Performance** | ✅ Native speed | ⚡ Browser-dependent |
| **Offline Usage** | ✅ Fully offline | ❌ Requires server |
| **File Access** | ✅ Native file system | ⚠️ Limited downloads |
| **Installation** | ⚠️ Requires build | ✅ Just open browser |
| **Updates** | ⚠️ Manual rebuild | ✅ Automatic |
| **Resource Usage** | ✅ Lower memory | ⚠️ Browser overhead |

### Interface Components

The desktop app includes all the same components as the web interface:
- **Circuit Designer**: Build and modify quantum circuits
- **Resource Estimator**: Calculate quantum resource requirements
- **Provider Comparison**: Compare across quantum hardware vendors
- **Visualization Tools**: Interactive charts and circuit diagrams
- **Export Capabilities**: Save results in multiple formats
