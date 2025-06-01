"""
Orquestra Python SDK
====================

A Python Software Development Kit for interacting with the Orquestra Quantum Resource
Estimation platform. This SDK provides tools for defining quantum circuits, modeling
hardware architectures, performing resource estimations, and integrating with
quantum hardware providers.

Key Modules and Classes:
------------------------
- `circuit`: Defines `QuantumCircuit` and `QuantumGate` for representing quantum programs.
- `hardware`: Defines `QuantumHardwareArchitecture` for modeling physical quantum devices.
- `estimation`: Provides `estimate_all_quantum_resources` for comprehensive resource analysis
  and `QuantumResourceEstimationResults` for holding the results.
- `providers`: Contains interfaces and utilities for integrating with various quantum
  hardware providers.
- `exceptions`: Custom exceptions used by the SDK.

Example Usage:
--------------
```python
from orquestra import (
    QuantumCircuit,
    QuantumGate,
    QuantumHardwareArchitecture,
    estimate_all_quantum_resources,
    ConnectivityType
)

# Define a simple Bell state circuit
bell_circuit = QuantumCircuit(
    id="bell_state",
    name="Bell State Preparation",
    qubits=2,
    gates=[
        QuantumGate(id="h0", type="H", qubits=[0]),
        QuantumGate(id="cx01", type="CNOT", qubits=[0, 1]),
    ]
)

# Define a model for a hypothetical hardware architecture
example_architecture = QuantumHardwareArchitecture(
    name="Hypothetical_NISQ_Device_v1",
    qubit_count=5,
    connectivity=ConnectivityType.LINEAR, # Using the enum member
    native_gate_set=["X", "Y", "Z", "H", "CNOT", "RZ"],
    gate_errors={
        "single-qubit": 1e-3,
        "two-qubit": 5e-3,
        "H": 1.1e-3,
        "CNOT": 5.5e-3,
    },
    readout_errors=[1e-2] * 5, # Per-qubit readout error
    t1_times=[100.0] * 5,      # T1 in microseconds
    t2_times=[80.0] * 5,       # T2 in microseconds
    gate_timings={
        "single-qubit": 30,   # ns
        "two-qubit": 200,     # ns
        "measurement": 500,   # ns
    }
)

# Perform resource estimation
try:
    estimation_results = estimate_all_quantum_resources(
        circuit=bell_circuit,
        architecture=example_architecture,
        options={
            "enable_fault_tolerance": False,
            "routing_algorithm": "greedy-router"
        }
    )
    print(f"Estimation for '{bell_circuit.name}' on '{example_architecture.name}':")
    print(f"  Total Gates: {estimation_results.total_gate_count}")
    print(f"  Circuit Depth: {estimation_results.circuit_depth}")
    print(f"  Estimated Fidelity: {estimation_results.circuit_fidelity:.4f}")
    if estimation_results.optimization_suggestions:
        print("  Suggestions:")
        for suggestion in estimation_results.optimization_suggestions:
            print(f"    - {suggestion}")

except Exception as e:
    print(f"An error occurred: {e}")

```

For more detailed information, please refer to the specific module documentation
and the main Orquestra platform documentation.
"""

import logging

# Define the SDK version
__version__ = "0.1.0"

# --- Import key classes and functions for easier access ---

# From circuit.py
from .circuit import QuantumGate, QuantumCircuit

# From hardware.py
from .hardware import (
    QuantumHardwareArchitecture,
    ConnectivityType,
    GateErrorModel,
    GateTimingsModel,
    HardwareConstraintsModel,
    CustomConnectivityModel
)

# From estimation.py
from .estimation import (
    QuantumResourceEstimationResults,
    FaultToleranceResults,
    SwapOverheadResults,
    CoherenceTimeResults,
    CoherenceLimitedResults,
    EstimationOptions,
    estimate_all_quantum_resources,
    calculate_circuit_logical_depth, # Exposing core calculation functions might be useful
    analyze_gate_composition,
    estimate_quantum_volume_for_circuit,
    estimate_swap_overhead_count,
    estimate_physical_execution_time,
    calculate_required_coherence,
    estimate_circuit_fidelity,
    estimate_fault_tolerant_resources,
    estimate_classical_resources,
    generate_optimization_suggestions
)

# From providers.py (if base classes or common utilities are defined)
# Example:
# from .providers import BaseHardwareProvider, ProviderIntegrationError
# For now, assuming it might not have top-level exports or will be added later.

# From exceptions.py
from .exceptions import (
    OrquestraSDKError,
    CircuitValidationError,
    HardwareDefinitionError,
    EstimationError,
    ProviderIntegrationError,
    ConfigurationError
)

# --- Define __all__ for `from orquestra import *` ---
# It's generally good practice to explicitly list what's exported.
__all__ = [
    # Version
    "__version__",
    # Circuit module
    "QuantumGate",
    "QuantumCircuit",
    # Hardware module
    "QuantumHardwareArchitecture",
    "ConnectivityType",
    "GateErrorModel",
    "GateTimingsModel",
    "HardwareConstraintsModel",
    "CustomConnectivityModel",
    # Estimation module
    "QuantumResourceEstimationResults",
    "FaultToleranceResults",
    "SwapOverheadResults",
    "CoherenceTimeResults",
    "CoherenceLimitedResults",
    "EstimationOptions",
    "estimate_all_quantum_resources",
    "calculate_circuit_logical_depth",
    "analyze_gate_composition",
    "estimate_quantum_volume_for_circuit",
    "estimate_swap_overhead_count",
    "estimate_physical_execution_time",
    "calculate_required_coherence",
    "estimate_circuit_fidelity",
    "estimate_fault_tolerant_resources",
    "estimate_classical_resources",
    "generate_optimization_suggestions",
    # Exceptions module
    "OrquestraSDKError",
    "CircuitValidationError",
    "HardwareDefinitionError",
    "EstimationError",
    "ProviderIntegrationError",
    "ConfigurationError",
    # Logger
    "get_orquestra_logger",
]

# --- Setup a default logger for the SDK ---
# Users can configure this logger if they need more control.
_SDK_LOGGER_NAME = "orquestra_sdk"

def get_orquestra_logger(name: str = _SDK_LOGGER_NAME) -> logging.Logger:
    """
    Retrieves a logger instance for the Orquestra SDK.

    This function provides a centralized way to get a logger, ensuring consistent
    naming and allowing for potential future centralized logging configuration.

    Args:
        name: The name of the logger. Defaults to 'orquestra_sdk'.

    Returns:
        A logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        # Add a default null handler to prevent "No handler found" warnings
        # if the user of the library doesn't configure logging.
        logger.addHandler(logging.NullHandler())
    return logger

# Initialize a default logger instance that can be used by modules within the SDK
logger = get_orquestra_logger()

logger.info(f"Orquestra SDK v{__version__} initialized.")

# Clean up namespace to avoid exposing 'logging' directly if not intended
# However, 'logger' instance is fine to expose if modules use it.
# del logging
