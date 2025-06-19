"""
Unit tests for the core quantum module.
"""

import pytest
from orquestra_qre.quantum import (
    QuantumGate, 
    QuantumCircuit,
    ResourceEstimate,
    QuantumResourceEstimator,
    CircuitGenerator
)


class TestQuantumGate:
    """Test the QuantumGate class."""
    
    def test_gate_initialization(self):
        """Test that gates are properly initialized."""
        # Simple gate without parameters
        gate1 = QuantumGate("H", [0])
        assert gate1.name == "H"
        assert gate1.qubits == [0]
        assert gate1.parameters is None
        
        # Gate with parameters
        gate2 = QuantumGate("RZ", [1], [0.5])
        assert gate2.name == "RZ"
        assert gate2.qubits == [1]
        assert gate2.parameters == [0.5]
        
        # Two-qubit gate
        gate3 = QuantumGate("CNOT", [0, 1])
        assert gate3.name == "CNOT"
        assert gate3.qubits == [0, 1]
        assert gate3.parameters is None
    
    def test_gate_to_dict(self):
        """Test the to_dict method."""
        gate = QuantumGate("H", [0])
        gate_dict = gate.to_dict()
        
        assert isinstance(gate_dict, dict)
        assert gate_dict["name"] == "H"
        assert gate_dict["qubits"] == [0]
        assert gate_dict["parameters"] == []
        
        # Gate with parameters
        gate = QuantumGate("RZ", [1], [0.5])
        gate_dict = gate.to_dict()
        assert gate_dict["parameters"] == [0.5]


class TestQuantumCircuit:
    """Test the QuantumCircuit class."""
    
    def test_circuit_initialization(self):
        """Test that circuits are properly initialized."""
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        
        circuit = QuantumCircuit(2, gates, "Test Circuit")
        
        assert circuit.num_qubits == 2
        assert len(circuit.gates) == 2
        assert circuit.name == "Test Circuit"
        
        # Default name when not provided
        circuit = QuantumCircuit(2, gates)
        assert circuit.name == "Quantum Circuit"
    
    def test_circuit_to_dict(self):
        """Test the to_dict method."""
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        
        circuit = QuantumCircuit(2, gates, "Test Circuit")
        circuit_dict = circuit.to_dict()
        
        assert isinstance(circuit_dict, dict)
        assert circuit_dict["name"] == "Test Circuit"
        assert circuit_dict["num_qubits"] == 2
        assert len(circuit_dict["gates"]) == 2
        assert circuit_dict["depth"] == 2
    
    def test_get_depth(self):
        """Test the depth calculation."""
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("X", [1]),
            QuantumGate("CNOT", [0, 1])
        ]
        
        circuit = QuantumCircuit(2, gates)
        assert circuit.get_depth() == 3


class TestResourceEstimate:
    """Test the ResourceEstimate class."""
    
    def test_estimate_initialization(self):
        """Test that resource estimates are properly initialized."""
        estimate = ResourceEstimate(
            circuit_name="Test Circuit",
            num_qubits=2,
            gate_count=3,
            depth=2,
            estimated_runtime_ms=25.0,
            estimated_fidelity=0.95,
            gate_breakdown={"H": 1, "CNOT": 1, "X": 1}
        )
        
        assert estimate.circuit_name == "Test Circuit"
        assert estimate.num_qubits == 2
        assert estimate.gate_count == 3
        assert estimate.depth == 2
        assert estimate.estimated_runtime_ms == 25.0
        assert estimate.estimated_fidelity == 0.95
        assert estimate.gate_breakdown == {"H": 1, "CNOT": 1, "X": 1}
    
    def test_estimate_to_dict(self):
        """Test the to_dict method."""
        estimate = ResourceEstimate(
            circuit_name="Test Circuit",
            num_qubits=2,
            gate_count=3,
            depth=2,
            estimated_runtime_ms=25.0,
            estimated_fidelity=0.95,
            gate_breakdown={"H": 1, "CNOT": 1, "X": 1}
        )
        
        estimate_dict = estimate.to_dict()
        
        assert isinstance(estimate_dict, dict)
        assert estimate_dict["circuit_name"] == "Test Circuit"
        assert estimate_dict["num_qubits"] == 2
        assert estimate_dict["gate_count"] == 3
        assert estimate_dict["depth"] == 2
        assert estimate_dict["estimated_runtime_ms"] == 25.0
        assert estimate_dict["estimated_fidelity"] == 0.95
        assert estimate_dict["gate_breakdown"] == {"H": 1, "CNOT": 1, "X": 1}


class TestQuantumResourceEstimator:
    """Test the QuantumResourceEstimator class."""
    
    def test_estimator_initialization(self):
        """Test that the estimator is properly initialized."""
        estimator = QuantumResourceEstimator()
        
        # Check that gate costs are initialized
        assert "H" in estimator.gate_costs
        assert "CNOT" in estimator.gate_costs
        assert estimator.gate_costs["H"] == 1.0
        assert estimator.gate_costs["CNOT"] == 2.5
    
    def test_estimate_resources(self):
        """Test the resource estimation for a simple circuit."""
        estimator = QuantumResourceEstimator()
        
        # Create a simple Bell state circuit
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        circuit = QuantumCircuit(2, gates, "Bell State")
        
        # Estimate resources
        estimate = estimator.estimate_resources(circuit)
        
        # Validate the estimate
        assert estimate.circuit_name == "Bell State"
        assert estimate.num_qubits == 2
        assert estimate.gate_count == 2
        assert estimate.depth == 2
        
        # Check gate breakdown
        assert "H" in estimate.gate_breakdown
        assert "CNOT" in estimate.gate_breakdown
        assert estimate.gate_breakdown["H"] == 1
        assert estimate.gate_breakdown["CNOT"] == 1
        
        # Check that runtime and fidelity were calculated
        assert estimate.estimated_runtime_ms > 0
        assert 0 < estimate.estimated_fidelity <= 1.0


class TestCircuitGenerator:
    """Test the CircuitGenerator class."""
    
    def test_generate_bell_state(self):
        """Test the Bell state circuit generation."""
        generator = CircuitGenerator()
        circuit = generator.generate_bell_state()
        
        assert circuit.name == "Bell State"
        assert circuit.num_qubits == 2
        assert len(circuit.gates) == 2
        assert circuit.gates[0].name == "H"
        assert circuit.gates[1].name == "CNOT"
    
    def test_generate_grover_search(self):
        """Test the Grover search circuit generation."""
        generator = CircuitGenerator()
        
        # Test with default parameters
        circuit = generator.generate_grover_search()
        assert circuit.name == "Grover Search (3 qubits)"
        assert circuit.num_qubits == 3
        assert len(circuit.gates) > 0
        
        # Test with custom qubit count
        circuit = generator.generate_grover_search(4)
        assert circuit.name == "Grover Search (4 qubits)"
        assert circuit.num_qubits == 4
    
    def test_generate_qft(self):
        """Test the QFT circuit generation."""
        generator = CircuitGenerator()
        
        # Test with default parameters
        circuit = generator.generate_qft()
        assert circuit.name == "QFT (3 qubits)"
        assert circuit.num_qubits == 3
        assert len(circuit.gates) > 0
        
        # Test with custom qubit count
        circuit = generator.generate_qft(4)
        assert circuit.name == "QFT (4 qubits)"
        assert circuit.num_qubits == 4
    
    def test_generate_random_circuit(self):
        """Test the random circuit generation."""
        generator = CircuitGenerator()
        
        # Test with default parameters
        circuit = generator.generate_random_circuit()
        assert "Random Circuit" in circuit.name
        assert circuit.num_qubits == 4
        assert len(circuit.gates) == 10
        
        # Test with custom parameters
        circuit = generator.generate_random_circuit(5, 15)
        assert "Random Circuit" in circuit.name
        assert circuit.num_qubits == 5
        assert len(circuit.gates) == 15
        
        # Check that randomization works by generating multiple circuits
        # They should have different gates (with high probability)
        circuit1 = generator.generate_random_circuit(4, 10)
        circuit2 = generator.generate_random_circuit(4, 10)
        
        # Convert gates to string representations for comparison
        gates1 = [f"{g.name}:{g.qubits}" for g in circuit1.gates]
        gates2 = [f"{g.name}:{g.qubits}" for g in circuit2.gates]
        
        # Circuits should differ in at least one gate (with very high probability)
        assert gates1 != gates2
