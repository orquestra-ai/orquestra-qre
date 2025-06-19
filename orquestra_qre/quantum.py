"""Quantum circuit generation and resource estimation."""

import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class QuantumGate:
    """Represents a quantum gate."""
    name: str
    qubits: List[int]
    parameters: List[float] = None
    
    def to_dict(self):
        return {
            'name': self.name,
            'qubits': self.qubits,
            'parameters': self.parameters or []
        }


@dataclass
class QuantumCircuit:
    """Represents a quantum circuit."""
    num_qubits: int
    gates: List[QuantumGate]
    name: str = "Quantum Circuit"
    
    def to_dict(self):
        return {
            'name': self.name,
            'num_qubits': self.num_qubits,
            'gates': [gate.to_dict() for gate in self.gates],
            'depth': self.get_depth()
        }
    
    def get_depth(self):
        """Calculate circuit depth."""
        return len(self.gates)  # Simplified depth calculation


@dataclass
class ResourceEstimate:
    """Resource estimation results."""
    circuit_name: str
    num_qubits: int
    gate_count: int
    depth: int
    estimated_runtime_ms: float
    estimated_fidelity: float
    gate_breakdown: Dict[str, int]
    
    def to_dict(self):
        return {
            'circuit_name': self.circuit_name,
            'num_qubits': self.num_qubits,
            'gate_count': self.gate_count,
            'depth': self.depth,
            'estimated_runtime_ms': self.estimated_runtime_ms,
            'estimated_fidelity': self.estimated_fidelity,
            'gate_breakdown': self.gate_breakdown
        }


class QuantumResourceEstimator:
    """Quantum resource estimator."""
    
    def __init__(self):
        """Initialize the estimator."""
        self.gate_costs = {
            'H': 1.0,    # Hadamard
            'X': 0.8,    # Pauli-X
            'Y': 0.8,    # Pauli-Y
            'Z': 0.5,    # Pauli-Z
            'CNOT': 2.5, # Controlled-NOT
            'RZ': 1.2,   # Rotation-Z
            'RY': 1.2,   # Rotation-Y
            'RX': 1.2,   # Rotation-X
            'T': 0.9,    # T gate
            'S': 0.7,    # S gate
            'SWAP': 7.5  # SWAP gate (equivalent to 3 CNOTs)
        }
    
    def estimate_resources(self, circuit: QuantumCircuit, connectivity_model=None) -> ResourceEstimate:
        """
        Estimate resources for a quantum circuit.
        
        Args:
            circuit: The quantum circuit to analyze
            connectivity_model: Optional connectivity model to calculate SWAP overhead
        
        Returns:
            ResourceEstimate object with estimation results
        """
        gate_breakdown = {}
        total_cost = 0.0
        
        for gate in circuit.gates:
            gate_name = gate.name
            gate_breakdown[gate_name] = gate_breakdown.get(gate_name, 0) + 1
            total_cost += self.gate_costs.get(gate_name, 1.0)
        
        # Estimate runtime (simplified model)
        estimated_runtime = total_cost * 10.0  # 10ms per cost unit
        
        # Estimate fidelity (simplified model)
        fidelity_loss = min(0.1, total_cost * 0.001)
        estimated_fidelity = max(0.5, 1.0 - fidelity_loss)
        
        # Create basic resource estimation
        estimate = ResourceEstimate(
            circuit_name=circuit.name,
            num_qubits=circuit.num_qubits,
            gate_count=len(circuit.gates),
            depth=circuit.get_depth(),
            estimated_runtime_ms=estimated_runtime,
            estimated_fidelity=estimated_fidelity,
            gate_breakdown=gate_breakdown
        )
        
        # Add connectivity analysis if a model is provided
        if connectivity_model:
            from orquestra_qre.connectivity import SWAPEstimator
            
            # Analyze SWAP overhead
            swap_analysis = SWAPEstimator.estimate_swap_overhead(circuit, connectivity_model)
            
            # Add SWAP analysis to the estimate
            estimate.swap_analysis = swap_analysis
            
            # Adjust runtime and fidelity based on SWAP overhead
            if 'approx_swap_count' in swap_analysis:
                swap_count = swap_analysis['approx_swap_count']
                
                # Add SWAP gates to the gate breakdown
                if swap_count > 0:
                    gate_breakdown['SWAP'] = gate_breakdown.get('SWAP', 0) + swap_count
                
                # Add SWAPs to the total cost
                additional_cost = swap_count * self.gate_costs['SWAP']
                total_cost += additional_cost
                
                # Recalculate runtime
                estimated_runtime = total_cost * 10.0
                estimate.estimated_runtime_ms = estimated_runtime
                
                # Recalculate fidelity
                fidelity_loss = min(0.1, total_cost * 0.001)
                estimate.estimated_fidelity = max(0.5, 1.0 - fidelity_loss)
                
                # Update gate count and depth
                if 'routed_gate_count' in swap_analysis:
                    estimate.routed_gate_count = swap_analysis['routed_gate_count']
                if 'swap_depth_overhead' in swap_analysis:
                    estimate.depth_with_swaps = estimate.depth + swap_analysis['swap_depth_overhead']
        
        return estimate
        
        return ResourceEstimate(
            circuit_name=circuit.name,
            num_qubits=circuit.num_qubits,
            gate_count=len(circuit.gates),
            depth=circuit.get_depth(),
            estimated_runtime_ms=estimated_runtime,
            estimated_fidelity=estimated_fidelity,
            gate_breakdown=gate_breakdown
        )


class CircuitGenerator:
    """Generate example quantum circuits."""
    
    @staticmethod
    def generate_bell_state() -> QuantumCircuit:
        """Generate a Bell state circuit."""
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        return QuantumCircuit(2, gates, "Bell State")
    
    @staticmethod
    def generate_grover_search(n_qubits: int = 3) -> QuantumCircuit:
        """Generate a simplified Grover search circuit."""
        gates = []
        
        # Initialize superposition
        for i in range(n_qubits):
            gates.append(QuantumGate("H", [i]))
        
        # Oracle (simplified)
        gates.append(QuantumGate("Z", [n_qubits - 1]))
        
        # Diffusion operator (simplified)
        for i in range(n_qubits):
            gates.append(QuantumGate("H", [i]))
            gates.append(QuantumGate("X", [i]))
        
        gates.append(QuantumGate("H", [n_qubits - 1]))
        for i in range(n_qubits - 1):
            gates.append(QuantumGate("CNOT", [i, n_qubits - 1]))
        gates.append(QuantumGate("H", [n_qubits - 1]))
        
        for i in range(n_qubits):
            gates.append(QuantumGate("X", [i]))
            gates.append(QuantumGate("H", [i]))
        
        return QuantumCircuit(n_qubits, gates, f"Grover Search ({n_qubits} qubits)")
    
    @staticmethod
    def generate_qft(n_qubits: int = 3) -> QuantumCircuit:
        """Generate a Quantum Fourier Transform circuit."""
        gates = []
        
        for i in range(n_qubits):
            gates.append(QuantumGate("H", [i]))
            for j in range(i + 1, n_qubits):
                gates.append(QuantumGate("RZ", [j], [3.14159 / (2 ** (j - i))]))
                gates.append(QuantumGate("CNOT", [j, i]))
        
        return QuantumCircuit(n_qubits, gates, f"QFT ({n_qubits} qubits)")
    
    @staticmethod
    def generate_random_circuit(n_qubits: int = 4, n_gates: int = 10) -> QuantumCircuit:
        """Generate a random quantum circuit."""
        gates = []
        gate_types = ["H", "X", "Y", "Z", "RZ", "RY", "T", "S"]
        
        for _ in range(n_gates):
            if random.random() < 0.3 and n_qubits > 1:  # 30% chance for CNOT
                qubit1 = random.randint(0, n_qubits - 1)
                qubit2 = random.randint(0, n_qubits - 1)
                while qubit2 == qubit1:
                    qubit2 = random.randint(0, n_qubits - 1)
                gates.append(QuantumGate("CNOT", [qubit1, qubit2]))
            else:
                gate_type = random.choice(gate_types)
                qubit = random.randint(0, n_qubits - 1)
                if gate_type in ["RZ", "RY"]:
                    angle = random.uniform(0, 2 * 3.14159)
                    gates.append(QuantumGate(gate_type, [qubit], [angle]))
                else:
                    gates.append(QuantumGate(gate_type, [qubit]))
        
        return QuantumCircuit(n_qubits, gates, f"Random Circuit ({n_qubits}q, {n_gates}g)")
    
    @staticmethod
    def generate_vqe_circuit(n_qubits: int = 4, layers: int = 2, entanglement_pattern: str = "linear", ansatz_type: str = "hardware_efficient") -> QuantumCircuit:
        """Generate a Variational Quantum Eigensolver (VQE) circuit.
        
        This implementation uses an alternating layered ansatz with:
        1. Single-qubit rotations (Ry)
        2. Entangling CNOT gates in a hardware-efficient pattern
        
        Args:
            n_qubits: Number of qubits in the circuit
            layers: Number of variational layers
            entanglement_pattern: Pattern for entangling gates ('linear', 'circular', etc.)
            ansatz_type: Type of ansatz to use ('hardware_efficient', 'uccsd', etc.)
        
        Returns:
            A VQE circuit with the specified parameters
        """
        gates = []
        
        if ansatz_type == "uccsd":
            # Unitary Coupled Cluster Singles and Doubles (UCCSD) ansatz
            # This is a simplified implementation of UCCSD for demonstration
            
            # State preparation (initialize in reference state - all qubits in |0⟩ except first half in |1⟩)
            for i in range(n_qubits // 2):
                gates.append(QuantumGate("X", [i]))
            
            # UCCSD typically involves excitation operators
            for layer in range(layers):
                # Single excitations (simplified)
                for i in range(n_qubits // 2):
                    j = i + n_qubits // 2
                    if j < n_qubits:
                        # Simulate a single excitation operator
                        angle = 3.14159 / (layer + 1)
                        gates.append(QuantumGate("RY", [i], [angle/2]))
                        gates.append(QuantumGate("CNOT", [i, j]))
                        gates.append(QuantumGate("RY", [j], [-angle/2]))
                        gates.append(QuantumGate("CNOT", [i, j]))
                
                # Double excitations (simplified)
                if n_qubits >= 4:
                    for i in range(0, n_qubits-3, 2):
                        # Simulate a double excitation operator
                        angle = 3.14159 / (2 * (layer + 1))
                        gates.append(QuantumGate("RX", [i], [angle]))
                        gates.append(QuantumGate("CNOT", [i, i+1]))
                        gates.append(QuantumGate("CNOT", [i+1, i+2]))
                        gates.append(QuantumGate("CNOT", [i+2, i+3]))
                        gates.append(QuantumGate("RX", [i+3], [-angle]))
                        gates.append(QuantumGate("CNOT", [i+2, i+3]))
                        gates.append(QuantumGate("CNOT", [i+1, i+2]))
                        gates.append(QuantumGate("CNOT", [i, i+1]))
            
            # Add measurement preparation rotations
            for i in range(n_qubits):
                gates.append(QuantumGate("H", [i]))
                
            return QuantumCircuit(n_qubits, gates, f"VQE-UCCSD ({n_qubits} qubits, {layers} layers)")
            
        else:  # hardware_efficient or other default ansatz types
            # State preparation (initialize in superposition)
            for i in range(n_qubits):
                gates.append(QuantumGate("H", [i]))
            
            # Variational layers
            for layer in range(layers):
                # Single-qubit rotations with parameters
                for i in range(n_qubits):
                    angle = 3.14159 / 4 * (layer + 1) / layers
                    gates.append(QuantumGate("RY", [i], [angle]))
                
                # Entangling gates
                if entanglement_pattern == "linear":
                    for i in range(n_qubits - 1):
                        gates.append(QuantumGate("CNOT", [i, i + 1]))
                elif entanglement_pattern == "circular":
                    for i in range(n_qubits - 1):
                        gates.append(QuantumGate("CNOT", [i, i + 1]))
                    gates.append(QuantumGate("CNOT", [n_qubits - 1, 0]))
                elif entanglement_pattern == "full":
                    for i in range(n_qubits):
                        for j in range(i + 1, n_qubits):
                            gates.append(QuantumGate("CNOT", [i, j]))
                else:
                    # Default to linear if unknown pattern
                    for i in range(n_qubits - 1):
                        gates.append(QuantumGate("CNOT", [i, i + 1]))
                
                # Additional entangler for more complex ansatz in deeper layers
                if layer > 0 and entanglement_pattern in ("linear", "circular"):
                    gates.append(QuantumGate("CNOT", [n_qubits - 1, 0]))  # Periodic boundary
            
            # Final parameterized rotations
            for i in range(n_qubits):
                angle = 3.14159 / 2 * (i + 1) / n_qubits
                gates.append(QuantumGate("RZ", [i], [angle]))
            
            return QuantumCircuit(n_qubits, gates, f"VQE-HE ({n_qubits} qubits, {layers} layers, {entanglement_pattern} entanglement)")
    
    @staticmethod
    def generate_qaoa_circuit(n_qubits: int = 4, p_steps: int = 1, problem_type: str = "maxcut") -> QuantumCircuit:
        """Generate a Quantum Approximate Optimization Algorithm (QAOA) circuit.
        
        This implements a QAOA circuit for optimization problems:
        1. Hadamard layer for initialization
        2. Problem Hamiltonian (depends on problem_type)
        3. Mixer Hamiltonian (X rotations)
        Repeating steps 2-3 for p_steps
        
        Args:
            n_qubits: Number of qubits
            p_steps: Number of QAOA steps/repetitions
            problem_type: Type of optimization problem ('maxcut', 'maxsat', etc.)
            
        Returns:
            A QAOA circuit
        """
        gates = []
        
        # Initial state: superposition of all basis states
        for i in range(n_qubits):
            gates.append(QuantumGate("H", [i]))
        
        # QAOA repeating blocks
        for step in range(p_steps):
            # Problem Hamiltonian - depends on problem_type
            gamma = 0.1 + 0.8 * step / p_steps  # Example parameter
            
            # Convert problem_type to lowercase for case-insensitive comparison
            problem_type_lower = problem_type.lower()
            
            if problem_type_lower == "maxcut":
                # MaxCut problem: Implement ZZ interactions in a ring topology
                for i in range(n_qubits):
                    j = (i + 1) % n_qubits  # Ring topology - connect each qubit to its neighbor
                    
                    # Implement ZZ interaction: exp(-i * gamma * Z_i * Z_j)
                    gates.append(QuantumGate("CNOT", [i, j]))
                    gates.append(QuantumGate("RZ", [j], [2 * gamma]))
                    gates.append(QuantumGate("CNOT", [i, j]))
                    
            elif problem_type_lower == "number partitioning":
                # Number Partitioning Problem (simplified for demonstration)
                # Split numbers into two groups with equal sum
                for i in range(n_qubits):
                    # Weight proportional to position (simplified)
                    weight = (i + 1) / n_qubits
                    phase = gamma * weight
                    
                    # Apply phase based on weight
                    gates.append(QuantumGate("RZ", [i], [phase]))
                
                # Add interactions between qubits
                for i in range(n_qubits):
                    for j in range(i+1, n_qubits):
                        # Cross-term interactions
                        weight_i = (i + 1) / n_qubits
                        weight_j = (j + 1) / n_qubits
                        interaction = weight_i * weight_j * gamma * 0.5
                        
                        gates.append(QuantumGate("CNOT", [i, j]))
                        gates.append(QuantumGate("RZ", [j], [interaction]))
                        gates.append(QuantumGate("CNOT", [i, j]))
                        
            elif problem_type_lower == "random":
                # Random problem: Create random ZZ interactions
                import random
                
                # Choose random pairs of qubits for interactions
                n_interactions = min(n_qubits * 2, n_qubits * (n_qubits - 1) // 2)
                for _ in range(n_interactions):
                    i = random.randint(0, n_qubits - 1)
                    j = random.randint(0, n_qubits - 1)
                    while j == i:
                        j = random.randint(0, n_qubits - 1)
                    
                    # Random weight between 0.1 and 1.0
                    weight = 0.1 + 0.9 * random.random()
                    phase = gamma * weight
                    
                    gates.append(QuantumGate("CNOT", [i, j]))
                    gates.append(QuantumGate("RZ", [j], [phase]))
                    gates.append(QuantumGate("CNOT", [i, j]))
            
            else:
                # Default to MaxCut if problem_type is not recognized
                for i in range(n_qubits):
                    j = (i + 1) % n_qubits
                    gates.append(QuantumGate("CNOT", [i, j]))
                    gates.append(QuantumGate("RZ", [j], [2 * gamma]))
                    gates.append(QuantumGate("CNOT", [i, j]))
            
            # Mixer Hamiltonian - X rotations (same for all problem types)
            beta = 3.14159 / (p_steps + 1) * (step + 1)  # Example parameter
            for i in range(n_qubits):
                gates.append(QuantumGate("RX", [i], [2 * beta]))
        
        # Format the circuit name using the original problem_type parameter
        # This preserves the case as defined in the UI
        return QuantumCircuit(n_qubits, gates, f"QAOA-{problem_type} ({n_qubits} qubits, {p_steps} steps)")
