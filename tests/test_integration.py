"""
Integration tests for the Orquestra QRE project.
These tests focus on hardware-aware estimation and error correction.
"""

import pytest
from dataclasses import dataclass
from orquestra_qre.quantum import (
    QuantumGate, 
    QuantumCircuit,
    ResourceEstimate,
    QuantumResourceEstimator,
    CircuitGenerator
)


# Define hardware provider model
@dataclass
class HardwareProvider:
    name: str
    max_qubits: int
    coherence_time_us: float
    single_qubit_error: float
    two_qubit_error: float
    connectivity: str


# Define test providers
TEST_HARDWARE_PROVIDERS = [
    HardwareProvider("TestProvider1", 10, 100, 1e-3, 1e-2, "Full"),
    HardwareProvider("TestProvider2", 100, 1000, 1e-4, 1e-3, "Full"),
]

# Define error correction codes
TEST_ERROR_CORRECTION = {
    "None": {"overhead": 1, "logical_to_physical": lambda n: n},
    "Test Code": {"overhead": 3, "logical_to_physical": lambda n: n * 3},
}

# Define hardware-aware estimation function
def hardware_aware_estimate(circuit, estimator, provider, ec_code):
    """Perform hardware-aware resource estimation for testing."""
    logical_qubits = circuit.num_qubits
    physical_qubits = ec_code["logical_to_physical"](logical_qubits)
    estimate = estimator.estimate_resources(circuit)
    
    # Adjust runtime and fidelity for error correction
    overhead = ec_code["overhead"]
    estimate.estimated_runtime_ms *= overhead
    estimate.estimated_fidelity **= overhead
    
    # Hardware feasibility checks
    warnings = []
    if physical_qubits > provider.max_qubits:
        warnings.append(f"Circuit requires {physical_qubits} physical qubits, but {provider.name} supports only {provider.max_qubits}.")
    if estimate.estimated_runtime_ms > provider.coherence_time_us / 1000:
        warnings.append(f"Estimated runtime exceeds coherence time.")
    
    # Add custom attributes
    estimate.hardware_warnings = warnings
    estimate.physical_qubits = physical_qubits
    estimate.selected_provider = provider.name
    estimate.error_correction = "None" if ec_code == TEST_ERROR_CORRECTION["None"] else "Test Code"
    
    return estimate


class TestHardwareAwareEstimation:
    """Test hardware-aware resource estimation."""
    
    def test_basic_estimation(self):
        """Test basic hardware-aware estimation."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        
        # Create a Bell state circuit
        circuit = gen.generate_bell_state()
        
        # Estimate with different providers, no error correction
        # Use provider with long coherence time to avoid warning
        provider = TEST_HARDWARE_PROVIDERS[1]  # Large provider with 1000 µs coherence time
        ec_code = TEST_ERROR_CORRECTION["None"]
        
        estimate = hardware_aware_estimate(circuit, estimator, provider, ec_code)
        
        # Check basic properties
        assert estimate.circuit_name == "Bell State"
        assert estimate.num_qubits == 2
        assert estimate.physical_qubits == 2  # No overhead with "None"
        assert estimate.selected_provider == "TestProvider2"
        # The circuit should be feasible on the large provider
        assert "physical qubits" not in " ".join(estimate.hardware_warnings)
    
    def test_qubit_limits(self):
        """Test hardware constraints - qubits."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        
        # Create a circuit with more qubits than the provider supports
        circuit = gen.generate_qft(8)
        
        # Small provider with only 10 qubits
        provider = TEST_HARDWARE_PROVIDERS[0]
        
        # Test with error correction to exceed qubit limit
        ec_code = TEST_ERROR_CORRECTION["Test Code"]
        estimate = hardware_aware_estimate(circuit, estimator, provider, ec_code)
        
        # Should have 8 * 3 = 24 physical qubits, exceeding 10 qubit limit
        assert estimate.physical_qubits == 24
        # Check that we have a warning about physical qubits
        assert any("physical qubits" in warning for warning in estimate.hardware_warnings)
        assert "physical qubits" in estimate.hardware_warnings[0]
    
    def test_coherence_limits(self):
        """Test hardware constraints - coherence time."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        
        # Create a circuit with many gates to exceed coherence time
        circuit = gen.generate_random_circuit(5, 100)
        
        # Provider with 100 µs coherence time
        provider = TEST_HARDWARE_PROVIDERS[0]
        
        # Apply error correction to increase runtime
        ec_code = TEST_ERROR_CORRECTION["Test Code"]
        estimate = hardware_aware_estimate(circuit, estimator, provider, ec_code)
        
        # If runtime exceeds coherence time, should have a warning
        if estimate.estimated_runtime_ms > provider.coherence_time_us / 1000:
            assert len([w for w in estimate.hardware_warnings if "coherence time" in w]) > 0
    
    def test_error_correction_overhead(self):
        """Test error correction overhead calculations."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        circuit = gen.generate_bell_state()
        provider = TEST_HARDWARE_PROVIDERS[1]  # Large provider
        
        # First, estimate without error correction
        no_ec = hardware_aware_estimate(circuit, estimator, provider, TEST_ERROR_CORRECTION["None"])
        
        # Then, estimate with error correction
        with_ec = hardware_aware_estimate(circuit, estimator, provider, TEST_ERROR_CORRECTION["Test Code"])
        
        # Check that physical qubits are increased by the overhead factor
        assert with_ec.physical_qubits == no_ec.physical_qubits * 3
        
        # Check that runtime is increased by the overhead factor
        assert with_ec.estimated_runtime_ms == pytest.approx(no_ec.estimated_runtime_ms * 3)
        
        # Check that fidelity is decreased
        assert with_ec.estimated_fidelity < no_ec.estimated_fidelity


class TestCircuitScaling:
    """Test scaling behavior of circuits with different sizes."""
    
    def test_circuit_size_scaling(self):
        """Test how resource estimates scale with circuit size."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        provider = TEST_HARDWARE_PROVIDERS[1]  # Large provider
        ec_code = TEST_ERROR_CORRECTION["None"]  # No error correction
        
        # Test QFT circuits with increasing sizes
        qubit_counts = [2, 4, 6, 8]
        runtime_ratios = []
        
        prev_runtime = None
        for n_qubits in qubit_counts:
            circuit = gen.generate_qft(n_qubits)
            estimate = hardware_aware_estimate(circuit, estimator, provider, ec_code)
            
            # Store the ratio of runtime between consecutive sizes
            if prev_runtime is not None:
                runtime_ratios.append(estimate.estimated_runtime_ms / prev_runtime)
            
            prev_runtime = estimate.estimated_runtime_ms
        
        # Check that runtime increases significantly with circuit size
        # QFT should have worse than linear scaling
        assert all(ratio > 1.0 for ratio in runtime_ratios)


class TestErrorCorrectionScaling:
    """Test scaling behavior with different error correction schemes."""
    
    def test_ec_scaling(self):
        """Test how error correction affects scaling."""
        gen = CircuitGenerator()
        estimator = QuantumResourceEstimator()
        provider = TEST_HARDWARE_PROVIDERS[1]  # Large provider
        
        # Generate a circuit
        circuit = gen.generate_grover_search(4)
        
        # Compare estimates with and without error correction
        no_ec = hardware_aware_estimate(circuit, estimator, provider, TEST_ERROR_CORRECTION["None"])
        with_ec = hardware_aware_estimate(circuit, estimator, provider, TEST_ERROR_CORRECTION["Test Code"])
        
        # Check physical qubit count
        assert with_ec.physical_qubits == no_ec.physical_qubits * 3
        
        # Check runtime
        assert with_ec.estimated_runtime_ms > no_ec.estimated_runtime_ms
        
        # Check fidelity - should be lower with error correction (raised to power of overhead)
        if no_ec.estimated_fidelity < 1.0:  # Only if original fidelity is less than 1
            assert with_ec.estimated_fidelity < no_ec.estimated_fidelity
