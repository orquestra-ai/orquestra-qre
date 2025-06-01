"""
Orquestra SDK: Quantum Resource Estimation Algorithms
----------------------------------------------------

This module implements the core algorithms for quantum resource estimation,
translating and adapting the logic from the Orquestra platform's TypeScript
metrics engine. It provides functions to analyze quantum circuits against
hardware architecture models to predict various performance and resource metrics.
"""
import math
from typing import List, Optional, Dict, Any, Union, Literal, Tuple
from enum import Enum
import collections # For deque in BFS

from pydantic import BaseModel, Field # Updated Pydantic imports

from .circuit import QuantumCircuit, QuantumGate
from .hardware import QuantumHardwareArchitecture, ConnectivityType, CustomConnectivityModel
from .exceptions import EstimationError, ConfigurationError

# --- Constants and Benchmarks ---

DEFAULT_PHYSICAL_ERROR_RATE: float = 1e-3
COHERENCE_SAFETY_FACTOR: float = 5.0

SURFACE_CODE_PARAMS: Dict[str, Any] = {
    "THRESHOLD_ERROR_RATE": 1e-2,
    "CONSTANT_FACTOR_A": 0.1,
    "PHYSICAL_PER_LOGICAL_FACTOR_FUNC": lambda d: 2 * d * d,
    "ROUTING_OVERHEAD_FACTOR": 1.5,
    "LOGICAL_CYCLE_TIME_FACTOR_VS_PHYSICAL_GATE": lambda d: 5 * d,
}

TECHNOLOGY_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "superconducting": {
        "gate_timings": {'single_qubit': 30.0, 'two_qubit': 200.0, 'measurement': 500.0},
        "gate_errors": {'single_qubit': 1e-4, 'two_qubit': 5e-3},
        "readout_errors": [1e-2],
        "t1_times": [100.0], "t2_times": [80.0],
    },
    "trapped_ion": {
        "gate_timings": {'single_qubit': 1000.0, 'two_qubit': 50000.0, 'measurement': 100000.0},
        "gate_errors": {'single_qubit': 5e-5, 'two_qubit': 1e-3},
        "readout_errors": [5e-3],
        "t1_times": [1e6], "t2_times": [1e5],
    },
    "photonic": {
        "gate_timings": {'single_qubit': 10.0, 'two_qubit': 100.0, 'measurement': 1000.0},
        "gate_errors": {'single_qubit': 1e-3, 'two_qubit': 1e-2, 'photon_loss': 0.01},
        "readout_errors": [2e-2],
        "t1_times": [float('inf')], "t2_times": [float('inf')],
    },
}

# --- Pydantic Models for Estimation Results and Options ---

class SwapOverheadResults(BaseModel):
    """Results for SWAP gate overhead estimation."""
    count: int = Field(..., description="Estimated number of SWAP gates needed.")
    algorithm: Literal['shortest-path', 'greedy-router', 'none'] = Field(
        ..., description="Algorithm used for SWAP estimation."
    )

class CoherenceTimeResults(BaseModel):
    """Required coherence times."""
    t1: float = Field(..., description="Required T1 relaxation time in microseconds (µs).")
    t2: float = Field(..., description="Required T2 dephasing time in microseconds (µs).")

class CoherenceLimitedResults(BaseModel):
    """Indicates if execution is likely limited by coherence times."""
    t1: bool = Field(..., description="True if execution is likely T1 limited.")
    t2: bool = Field(..., description="True if execution is likely T2 limited.")

class FaultToleranceResults(BaseModel):
    """Results for fault-tolerance analysis."""
    is_enabled: bool = Field(..., description="Whether fault-tolerance analysis was performed.")
    target_logical_error_rate: float = Field(..., description="Target error rate per logical qubit per logical gate cycle.")
    code_name: str = Field(..., description="Name of the error correction code used (e.g., 'SurfaceCode').")
    code_distance: float = Field(..., description="Estimated code distance 'd' required. Can be float('inf').") # float for inf
    logical_qubits: int = Field(..., description="Number of logical qubits.")
    physical_qubits_per_logical: float = Field(..., description="Number of physical qubits per logical qubit. Can be float('inf').")
    total_physical_qubits: float = Field(..., description="Total number of physical qubits required. Can be float('inf').")
    error_correction_overhead_factor: float = Field(..., description="Overall overhead factor (N_P / N_L). Can be float('inf').")
    logical_time_unit_duration: float = Field(..., description="Duration of one logical gate cycle in nanoseconds. Can be float('inf').")
    logical_depth: int = Field(..., description="Number of logical time steps or depth in terms of logical operations.")
    total_logical_execution_time: float = Field(..., description="Total execution time in terms of logical gate cycles (ns). Can be float('inf').")
    resource_state_count: float = Field(..., description="Number of magic states or other resource states required. Can be float('inf').")
    distillation_overhead: Optional[float] = Field(default=None, description="Overhead factor for magic state distillation. Can be float('inf').")

class QuantumResourceEstimationResults(BaseModel):
    """Comprehensive results of quantum resource estimation."""
    # Basic Circuit Metrics
    circuit_width: int = Field(..., description="N_q: Number of qubits used by the circuit.")
    circuit_depth: int = Field(..., description="D: Number of layers in the circuit (logical depth).")
    gate_counts: Dict[str, int] = Field(..., description="Breakdown of gate types and their counts.")
    total_gate_count: int = Field(..., description="Total number of gates in the circuit.")

    # Advanced Circuit Metrics
    t_gate_count: int = Field(..., description="N_T: Number of T-gates (critical for FTQC).")
    clifford_gate_count: int = Field(..., description="Number of Clifford gates.")
    non_clifford_gate_count: int = Field(..., description="Number of non-Clifford gates.")
    two_qubit_gate_count: int = Field(..., description="Total number of two-qubit gates.")
    multi_qubit_gate_count: int = Field(..., description="Total number of gates acting on >2 qubits.")

    # Hardware Interaction Metrics
    swap_overhead: SwapOverheadResults
    compiled_circuit_depth: Optional[int] = Field(default=None, description="D_compiled: Estimated depth after SWAP insertion and compilation.")
    quantum_volume_achievable: Optional[int] = Field(default=None, description="QV: Estimated Quantum Volume for this circuit size on this architecture.")

    # Time and Coherence Analysis
    estimated_execution_time_physical: float = Field(..., description="T_exec: Total physical execution time (nanoseconds).")
    required_coherence_time: CoherenceTimeResults
    coherence_limited: CoherenceLimitedResults

    # Error and Fidelity Analysis
    circuit_fidelity: float = Field(..., ge=0.0, le=1.0, description="F_circuit: Probability of error-free execution (0-1).")
    circuit_error_rate: float = Field(..., ge=0.0, le=1.0, description="ε_circuit = 1 - F_circuit.")
    dominant_error_source: Optional[str] = Field(default=None, description="Heuristic: 'gate_errors', 'readout_errors', 'decoherence'.")
    noise_resilience_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Heuristic score (0-1) of circuit's resilience.")

    # Classical Resource Analysis
    classical_preprocessing_complexity: Optional[str] = Field(default=None, description="Big-O notation for classical setup.")
    classical_memory_for_simulation_mb: Optional[float] = Field(default=None, description="Estimated memory for state-vector simulation (MB).")
    classical_control_complexity: Optional[str] = Field(default=None, description="Complexity of classical control systems.")

    # Fault-Tolerance Analysis
    fault_tolerance: Optional[FaultToleranceResults] = None

    # Optimization Suggestions
    optimization_suggestions: Optional[List[str]] = None

    analysis_timestamp: float = Field(..., description="Unix timestamp of when the analysis was performed.")

class EstimationOptions(BaseModel):
    """Options for configuring the resource estimation process."""
    routing_algorithm: Literal['shortest-path', 'greedy-router', 'none'] = Field(
        default='greedy-router', description="Algorithm for SWAP overhead estimation."
    )
    enable_fault_tolerance: bool = Field(
        default=False, description="Whether to perform fault-tolerance analysis."
    )
    target_logical_error_rate: float = Field(
        default=1e-15, gt=0.0, lt=1.0, description="Desired logical error rate for FTQC."
    )
    simulation_type: Literal['state-vector', 'tensor-network', 'clifford'] = Field(
        default='state-vector', description="Type of classical simulation to estimate resources for."
    )
    # Add other options as needed, e.g., specific initial mapping for SWAP
    initial_mapping: Optional[List[int]] = Field(default=None, description="Optional initial mapping of logical to physical qubits for SWAP estimation.")

    class Config:
        validate_assignment = True


# --- Core Circuit Analysis Functions ---

def calculate_circuit_logical_depth(circuit: QuantumCircuit) -> int:
    """Calculates the logical depth of a quantum circuit."""
    if not circuit.gates:
        return 0

    qubit_finish_layer = [0] * circuit.qubits
    max_depth = 0

    for gate in circuit.gates:
        current_gate_start_layer = 0
        for qubit_idx in gate.qubits:
            if not (0 <= qubit_idx < circuit.qubits):
                raise EstimationError(
                    f"Gate '{gate.id}' (type {gate.type}) acts on qubit {qubit_idx}, "
                    f"out of bounds for circuit with {circuit.qubits} qubits."
                )
            current_gate_start_layer = max(current_gate_start_layer, qubit_finish_layer[qubit_idx])
        
        gate_finish_layer = current_gate_start_layer + 1
        
        for qubit_idx in gate.qubits:
            qubit_finish_layer[qubit_idx] = gate_finish_layer
        
        max_depth = max(max_depth, gate_finish_layer)
            
    return max_depth

def analyze_gate_composition(circuit: QuantumCircuit) -> Dict[str, Any]:
    """Counts gate types and categories in the circuit."""
    gate_counts: Dict[str, int] = collections.defaultdict(int)
    t_gate_count = 0
    clifford_gate_count = 0
    non_clifford_gate_count = 0
    two_qubit_gate_count = 0
    multi_qubit_gate_count = 0

    CLIFFORD_GATES = {"X", "Y", "Z", "H", "S", "SDG", "CX", "CY", "CZ", "CNOT", "SWAP"} # Case-insensitive due to .upper()

    for gate in circuit.gates:
        gate_type_upper = gate.type.upper()
        gate_counts[gate_type_upper] += 1

        if gate_type_upper in ["T", "TDG"]:
            t_gate_count += 1
        
        if gate_type_upper in CLIFFORD_GATES:
            clifford_gate_count += 1
        else:
            non_clifford_gate_count += 1

        if len(gate.qubits) == 2:
            two_qubit_gate_count += 1
        elif len(gate.qubits) > 2:
            multi_qubit_gate_count += 1
            
    return {
        "gate_counts": dict(gate_counts),
        "total_gate_count": len(circuit.gates),
        "t_gate_count": t_gate_count,
        "clifford_gate_count": clifford_gate_count,
        "non_clifford_gate_count": non_clifford_gate_count,
        "two_qubit_gate_count": two_qubit_gate_count,
        "multi_qubit_gate_count": multi_qubit_gate_count,
    }

# --- Advanced Metrics Calculation ---

def estimate_quantum_volume_for_circuit(
    architecture: QuantumHardwareArchitecture,
    circuit_width: int
) -> int:
    """Estimates Quantum Volume achievable for a given circuit width on an architecture."""
    if circuit_width <= 0: return 1
    effective_circuit_width = min(circuit_width, architecture.qubit_count)

    effective_n = 0
    for n in range(1, effective_circuit_width + 1):
        num_two_qubit_gates_in_layer = n // 2
        num_single_qubit_gates_in_layer = n
        
        avg_single_qubit_error = architecture.get_gate_error("SINGLE-QUBIT", 1) # Generic type
        avg_two_qubit_error = architecture.get_gate_error("TWO-QUBIT", 2)   # Generic type

        single_qubit_fidelity_layer = math.pow(1 - avg_single_qubit_error, num_single_qubit_gates_in_layer)
        two_qubit_fidelity_layer = math.pow(1 - avg_two_qubit_error, num_two_qubit_gates_in_layer)
        layer_fidelity = single_qubit_fidelity_layer * two_qubit_fidelity_layer

        circuit_fidelity_without_readout = math.pow(layer_fidelity, n) # Depth is n
        
        avg_readout_error = 0.0
        if isinstance(architecture.readout_errors, list) and architecture.readout_errors:
            avg_readout_error = sum(architecture.readout_errors) / len(architecture.readout_errors)
        elif isinstance(architecture.readout_errors, (float,int)):
            avg_readout_error = float(architecture.readout_errors)
        else: # Fallback
            avg_readout_error = DEFAULT_PHYSICAL_ERROR_RATE * 5

        readout_fidelity = math.pow(1 - avg_readout_error, n)
        total_circuit_fidelity = circuit_fidelity_without_readout * readout_fidelity

        if total_circuit_fidelity > 2/3:
            effective_n = n
        else:
            break
            
    return int(math.pow(2, effective_n))

def _build_adjacency_list(architecture: QuantumHardwareArchitecture) -> List[List[int]]:
    """Helper to build adjacency list from architecture connectivity."""
    adj: List[List[int]] = [[] for _ in range(architecture.qubit_count)]

    if isinstance(architecture.connectivity, CustomConnectivityModel):
        # Validate custom connectivity again just in case, or rely on Pydantic
        if len(architecture.connectivity.adjacencies) != architecture.qubit_count:
            raise ConfigurationError(
                f"Custom connectivity adjacencies length ({len(architecture.connectivity.adjacencies)}) "
                f"does not match qubit_count ({architecture.qubit_count})."
            )
        # Basic copy, assuming CustomConnectivityModel validator ensures symmetry and bounds
        return [list(neighbors) for neighbors in architecture.connectivity.adjacencies]

    conn_type = architecture.connectivity # Enum member
    n = architecture.qubit_count

    if conn_type == ConnectivityType.ALL_TO_ALL:
        for i in range(n):
            for j in range(i + 1, n):
                adj[i].append(j)
                adj[j].append(i)
    elif conn_type == ConnectivityType.LINEAR:
        for i in range(n - 1):
            adj[i].append(i + 1)
            adj[i + 1].append(i)
    elif conn_type == ConnectivityType.RING:
        for i in range(n):
            adj[i].append((i + 1) % n)
            adj[(i + 1) % n].append(i) # Ensure symmetry for ring
    elif conn_type == ConnectivityType.GRID:
        side = math.ceil(math.sqrt(n))
        for r in range(side):
            for c in range(side):
                idx = r * side + c
                if idx >= n: continue
                # Right neighbor
                if c + 1 < side and (idx + 1) < n:
                    adj[idx].append(idx + 1)
                    adj[idx + 1].append(idx)
                # Down neighbor
                if r + 1 < side and (idx + side) < n:
                    adj[idx].append(idx + side)
                    adj[idx + side].append(idx)
    elif conn_type in [ConnectivityType.HEAVY_HEX, ConnectivityType.HEAVY_SQUARE]:
        # Simplified fallback for these complex topologies (e.g., linear-like with some cross-links)
        # A production SDK would need precise graph definitions for these.
        for i in range(n - 1):
            adj[i].append(i + 1)
            adj[i + 1].append(i)
            if i < n - 2 and (i % 3 == 0): # Add some cross-links
                adj[i].append(i + 2)
                adj[i + 2].append(i)
    else: # Should not happen if Pydantic validation is correct
        raise ConfigurationError(f"Unknown or unhandled connectivity type: {architecture.connectivity}")
    
    return [list(set(neighbors)) for neighbors in adj] # Ensure unique neighbors

def _shortest_path_distance(start_node: int, end_node: int, adj: List[List[int]]) -> float:
    """BFS for shortest path distance. Returns float for math.inf."""
    if start_node == end_node: return 0.0
    if not (0 <= start_node < len(adj) and 0 <= end_node < len(adj)):
        return math.inf # Node out of bounds

    queue = collections.deque([(start_node, 0)])
    visited = {start_node}

    while queue:
        curr, dist = queue.popleft()
        if curr == end_node:
            return float(dist)
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    return math.inf

def estimate_swap_overhead_count(
    circuit: QuantumCircuit,
    architecture: QuantumHardwareArchitecture,
    routing_algorithm: Literal['shortest-path', 'greedy-router', 'none'] = 'greedy-router',
    initial_mapping: Optional[List[int]] = None
) -> int:
    """Estimates SWAP gate overhead."""
    if architecture.connectivity == ConnectivityType.ALL_TO_ALL or routing_algorithm == 'none':
        return 0

    if circuit.qubits > architecture.qubit_count:
        raise EstimationError(
            f"Circuit requires {circuit.qubits} qubits, but architecture only has {architecture.qubit_count}."
        )

    adj = _build_adjacency_list(architecture)
    
    current_mapping: List[int] # logical_idx -> physical_idx
    if initial_mapping:
        if len(initial_mapping) != circuit.qubits:
            raise ConfigurationError("Initial mapping length must match circuit qubit count.")
        if len(set(initial_mapping)) != circuit.qubits:
            raise ConfigurationError("Initial mapping must contain unique physical qubit indices.")
        if not all(0 <= p_idx < architecture.qubit_count for p_idx in initial_mapping):
            raise ConfigurationError("Initial mapping contains physical qubit indices out of architecture bounds.")
        current_mapping = list(initial_mapping)
    else:
        current_mapping = list(range(circuit.qubits)) # Default linear mapping

    total_swaps = 0

    if routing_algorithm == 'shortest-path':
        for gate in circuit.gates:
            if len(gate.qubits) == 2:
                log_q1, log_q2 = gate.qubits
                phys_q1, phys_q2 = current_mapping[log_q1], current_mapping[log_q2]
                dist = _shortest_path_distance(phys_q1, phys_q2, adj)
                if dist > 1 and dist != math.inf:
                    total_swaps += int(dist - 1)
                elif dist == math.inf: # Should not happen if mapping is valid and graph connected
                    raise EstimationError(f"No path between physical qubits {phys_q1} and {phys_q2} for gate {gate.id}.")
    
    elif routing_algorithm == 'greedy-router':
        active_physical_qubits = set(current_mapping)
        for gate in circuit.gates:
            if len(gate.qubits) == 2:
                log_q1, log_q2 = gate.qubits
                phys_q1, phys_q2 = current_mapping[log_q1], current_mapping[log_q2]

                while phys_q1 not in adj[phys_q2]: # While not adjacent
                    current_dist = _shortest_path_distance(phys_q1, phys_q2, adj)
                    if current_dist <= 1 or current_dist == math.inf: break

                    best_swap_candidate: Optional[Tuple[int, int]] = None
                    min_new_distance = current_dist

                    # Try swapping phys_q1 with its neighbors
                    for neighbor_of_q1 in adj[phys_q1]:
                        if neighbor_of_q1 not in active_physical_qubits: continue
                        dist_after_swap = _shortest_path_distance(neighbor_of_q1, phys_q2, adj)
                        if dist_after_swap < min_new_distance:
                            min_new_distance = dist_after_swap
                            best_swap_candidate = (phys_q1, neighbor_of_q1)
                    
                    # Try swapping phys_q2 with its neighbors
                    for neighbor_of_q2 in adj[phys_q2]:
                        if neighbor_of_q2 not in active_physical_qubits: continue
                        dist_after_swap = _shortest_path_distance(phys_q1, neighbor_of_q2, adj)
                        # If this swap is better than swapping with phys_q1's neighbors
                        if dist_after_swap < min_new_distance:
                            min_new_distance = dist_after_swap
                            best_swap_candidate = (phys_q2, neighbor_of_q2)
                    
                    if best_swap_candidate:
                        total_swaps += 1
                        swapped_phys_a, swapped_phys_b = best_swap_candidate
                        
                        try:
                            log_at_swapped_a = current_mapping.index(swapped_phys_a)
                            log_at_swapped_b = current_mapping.index(swapped_phys_b)
                        except ValueError: # Should not happen if active_physical_qubits is correct
                             raise EstimationError("Internal error in greedy router: mapped qubit not found.")

                        current_mapping[log_at_swapped_a], current_mapping[log_at_swapped_b] = \
                            current_mapping[log_at_swapped_b], current_mapping[log_at_swapped_a]
                        
                        phys_q1, phys_q2 = current_mapping[log_q1], current_mapping[log_q2]
                    else: # No beneficial greedy SWAP found
                        dist_val = _shortest_path_distance(phys_q1, phys_q2, adj)
                        if dist_val > 1 and dist_val != math.inf : total_swaps += int(dist_val - 1)
                        break 
    return total_swaps

# --- Time, Coherence, and Error Analysis ---

def estimate_physical_execution_time(
    circuit: QuantumCircuit,
    architecture: QuantumHardwareArchitecture,
    swap_count: int,
    compiled_circuit_depth: Optional[int] = None
) -> float:
    """Estimates physical execution time in nanoseconds."""
    total_time_ns = 0.0
    
    # Default timings from architecture or global benchmarks
    default_single_q_time = architecture.get_gate_timing("SINGLE-QUBIT", 1)
    default_two_q_time = architecture.get_gate_timing("TWO-QUBIT", 2)
    default_meas_time = architecture.get_gate_timing("MEASUREMENT", 1) # Measurement is per qubit

    if compiled_circuit_depth is not None and compiled_circuit_depth > 0:
        # Simplified depth-based estimation: depth * slowest_typical_layer_time
        # Assume a layer is dominated by two-qubit gates or measurement if it's the final layer.
        # This is a heuristic.
        avg_layer_time = default_two_q_time # A common bottleneck
        total_time_ns = float(compiled_circuit_depth * avg_layer_time)
        # Add measurement time for all qubits at the end, assuming it's one layer
        total_time_ns += float(circuit.qubits * default_meas_time) # This might double count if depth includes measurement
                                                                # A more refined model would separate measurement depth.
                                                                # For now, let's assume compiled_circuit_depth is for gates only.
    else:
        # Sequential sum of gate times
        for gate in circuit.gates:
            num_q = len(gate.qubits)
            total_time_ns += architecture.get_gate_timing(gate.type, num_q)
        
        # Add SWAP time (SWAP = 3 CNOTs)
        cnot_timing = architecture.get_gate_timing("CNOT", 2) # Get CNOT specific or fallback
        swap_gate_duration = 3 * cnot_timing 
        total_time_ns += swap_count * swap_gate_duration
        
        # Add measurement time for all qubits at the end
        total_time_ns += circuit.qubits * default_meas_time
        
    return total_time_ns

def calculate_required_coherence(physical_execution_time_ns: float) -> CoherenceTimeResults:
    """Calculates required T1 and T2 in microseconds."""
    required_time_us = (physical_execution_time_ns / 1000.0) * COHERENCE_SAFETY_FACTOR
    return CoherenceTimeResults(t1=required_time_us, t2=required_time_us)

def estimate_circuit_fidelity(
    circuit: QuantumCircuit,
    architecture: QuantumHardwareArchitecture,
    swap_count: int
) -> float:
    """Estimates overall circuit fidelity."""
    total_fidelity = 1.0

    # Gate fidelities
    for gate in circuit.gates:
        num_q = len(gate.qubits)
        error_rate_g = gate.fidelity if gate.fidelity is not None else (1.0 - architecture.get_gate_error(gate.type, num_q))
        total_fidelity *= error_rate_g # error_rate_g is actually fidelity here if gate.fidelity is used
                                       # Let's clarify: get_gate_error returns error rate.
        actual_error_rate = architecture.get_gate_error(gate.type, num_q)
        if gate.fidelity is not None: # User provided fidelity overrides
             total_fidelity *= gate.fidelity
        else:
             total_fidelity *= (1.0 - actual_error_rate)


    # SWAP gate fidelities (SWAP = 3 CNOTs)
    cnot_error_rate = architecture.get_gate_error("CNOT", 2)
    swap_fidelity = math.pow(1.0 - cnot_error_rate, 3)
    total_fidelity *= math.pow(swap_fidelity, swap_count)

    # Readout fidelities
    avg_readout_error = 0.0
    if isinstance(architecture.readout_errors, list) and architecture.readout_errors:
        avg_readout_error = sum(architecture.readout_errors) / len(architecture.readout_errors)
    elif isinstance(architecture.readout_errors, (float,int)):
        avg_readout_error = float(architecture.readout_errors)
    else: # Fallback
        avg_readout_error = DEFAULT_PHYSICAL_ERROR_RATE * 5
    total_fidelity *= math.pow(1.0 - avg_readout_error, circuit.qubits)
    
    # Decoherence factor (heuristic)
    physical_time_ns = estimate_physical_execution_time(circuit, architecture, swap_count) # Re-estimate or pass in
    execution_time_us = physical_time_ns / 1000.0
    
    avg_t2_us = 0.0
    if isinstance(architecture.t2_times, list) and architecture.t2_times:
        avg_t2_us = sum(architecture.t2_times) / len(architecture.t2_times)
    elif isinstance(architecture.t2_times, (float,int)):
        avg_t2_us = float(architecture.t2_times)
    else: # Fallback
        avg_t2_us = float(TECHNOLOGY_BENCHMARKS["superconducting"]["t2_times"][0])

    if avg_t2_us > 0:
        decoherence_factor = math.exp(-execution_time_us / avg_t2_us)
        total_fidelity *= decoherence_factor
        
    return max(0.0, total_fidelity)

# --- Fault-Tolerance Analysis ---

def estimate_fault_tolerant_resources(
    logical_qubit_count: int,
    t_gate_count: int,
    logical_circuit_depth: int,
    architecture: QuantumHardwareArchitecture,
    target_logical_error_rate: float = 1e-15
) -> FaultToleranceResults:
    """Estimates fault-tolerant resources using Surface Code model."""
    physical_error_rate = architecture.get_gate_error("TWO-QUBIT", 2) # Dominant error

    if physical_error_rate >= SURFACE_CODE_PARAMS["THRESHOLD_ERROR_RATE"]:
        return FaultToleranceResults(
            is_enabled=True, target_logical_error_rate=target_logical_error_rate, code_name="SurfaceCode",
            code_distance=math.inf, logical_qubits=logical_qubit_count,
            physical_qubits_per_logical=math.inf, total_physical_qubits=math.inf,
            error_correction_overhead_factor=math.inf, logical_time_unit_duration=math.inf,
            logical_depth=logical_circuit_depth, total_logical_execution_time=math.inf,
            resource_state_count=math.inf, distillation_overhead=math.inf
        )

    log_base_val = physical_error_rate / SURFACE_CODE_PARAMS["THRESHOLD_ERROR_RATE"]
    log_val_val = target_logical_error_rate / SURFACE_CODE_PARAMS["CONSTANT_FACTOR_A"]

    if log_base_val <= 0 or log_base_val == 1.0 or log_val_val <= 0: # Avoid math domain errors
        d_float = float('inf')
    else:
        try:
            d_float = 2 * (math.log(log_val_val) / math.log(log_base_val)) - 1
        except ValueError: # e.g. log of negative number
            d_float = float('inf')

    if d_float == float('inf'):
        d = float('inf')
    else:
        d_ceil = math.ceil(d_float)
        d_int = int(d_ceil if d_ceil % 2 != 0 else d_ceil + 1)
        d = float(max(3, d_int))


    if d == float('inf'):
        physical_per_logical = float('inf')
        total_physical_qubits = float('inf')
        logical_time_unit_duration = float('inf')
        total_logical_execution_time = float('inf')
    else:
        physical_per_logical = float(SURFACE_CODE_PARAMS["PHYSICAL_PER_LOGICAL_FACTOR_FUNC"](d))
        total_physical_qubits_raw = logical_qubit_count * physical_per_logical
        total_physical_qubits = math.ceil(total_physical_qubits_raw * SURFACE_CODE_PARAMS["ROUTING_OVERHEAD_FACTOR"])
        
        physical_two_q_time = architecture.get_gate_timing("TWO-QUBIT", 2)
        logical_time_unit_duration = float(SURFACE_CODE_PARAMS["LOGICAL_CYCLE_TIME_FACTOR_VS_PHYSICAL_GATE"](d) * physical_two_q_time)
        total_logical_execution_time = logical_circuit_depth * logical_time_unit_duration

    resource_state_count = float(t_gate_count) # Can be inf if d is inf
    distillation_qubit_overhead = logical_qubit_count * 0.25 if resource_state_count > 0 and d != float('inf') else 0
    
    final_total_physical_qubits = total_physical_qubits if d == float('inf') else total_physical_qubits + math.ceil(distillation_qubit_overhead)

    return FaultToleranceResults(
        is_enabled=True, target_logical_error_rate=target_logical_error_rate, code_name="SurfaceCode",
        code_distance=d, logical_qubits=logical_qubit_count,
        physical_qubits_per_logical=physical_per_logical,
        total_physical_qubits=final_total_physical_qubits,
        error_correction_overhead_factor= (physical_per_logical * SURFACE_CODE_PARAMS["ROUTING_OVERHEAD_FACTOR"]) if d != float('inf') else float('inf'),
        logical_time_unit_duration=logical_time_unit_duration,
        logical_depth=logical_circuit_depth,
        total_logical_execution_time=total_logical_execution_time,
        resource_state_count=resource_state_count,
        distillation_overhead=1.25 if resource_state_count > 0 and d != float('inf') else (1.0 if d != float('inf') else float('inf'))
    )

# --- Classical Resource Analysis ---

def estimate_classical_resources(
    circuit: QuantumCircuit,
    simulation_type: Literal['state-vector', 'tensor-network', 'clifford'] = 'state-vector'
) -> Dict[str, Any]:
    """Estimates classical computational resources."""
    n = circuit.qubits
    g = len(circuit.gates)
    gate_comp = analyze_gate_composition(circuit)

    if simulation_type == 'clifford':
        if gate_comp["clifford_gate_count"] == gate_comp["total_gate_count"]:
            # Gottesman-Knill theorem
            mem_mb = math.ceil((n * n * 8) / (1024 * 1024)) + 1 # Stabilizer tableau
            return {"complexity": f"O(poly(N_q, G_total)) approx O(N_q^2 * G_total)", "memory_mb": mem_mb}
        else:
            simulation_type = 'state-vector' # Fallback for non-Clifford parts

    if simulation_type == 'state-vector':
        # Memory: 2^n complex numbers (16 bytes each for complex128)
        memory_bytes = math.pow(2, n) * 16
        memory_mb = math.ceil(memory_bytes / (1024 * 1024))
        return {"complexity": f"O(G_total * 2^N_q)", "memory_mb": memory_mb}

    if simulation_type == 'tensor-network':
        # Highly dependent on circuit structure
        return {
            "complexity": "Varies (e.g., O(poly(N_q) * D_max^k * G_total) for 1D-like)",
            "memory_mb": None, # Cannot give a generic number easily
        }
    return {"complexity": "Unknown", "memory_mb": None}

# --- Optimization Suggestions ---
def generate_optimization_suggestions(
    results: QuantumResourceEstimationResults,
    architecture: QuantumHardwareArchitecture
) -> List[str]:
    """Generates optimization suggestions based on estimation results."""
    suggestions: List[str] = []

    if results.swap_overhead.count > results.total_gate_count * 0.2:
        suggestions.append(
            f"High SWAP overhead ({results.swap_overhead.count} SWAPs). "
            f"Consider circuit re-compilation for '{architecture.name}' topology or alternative mappings."
        )
    if results.coherence_limited.t1 or results.coherence_limited.t2:
        suggestions.append(
            f"Execution likely coherence-limited. Aim to reduce circuit depth or use hardware with better coherence. "
            f"Required T1/T2: ~{results.required_coherence_time.t1:.1f}µs."
        )
    if results.circuit_fidelity < 0.9:
        suggestions.append(
            f"Low circuit fidelity ({(results.circuit_fidelity * 100):.1f}%). "
            "Explore error mitigation or fault-tolerant encoding if high precision is needed."
        )
    if results.fault_tolerance and results.fault_tolerance.is_enabled:
        ft = results.fault_tolerance
        if ft.total_physical_qubits != float('inf') and ft.total_physical_qubits > architecture.qubit_count * 50 :
             suggestions.append(f"Fault-tolerant mode requires very high physical qubit count ({ft.total_physical_qubits:,.0f}). Verify algorithm scale or target error rate.")
        if ft.t_gate_count > 0 and ft.resource_state_count != float('inf') and ft.resource_state_count / ft.t_gate_count > 1.5 : # type: ignore
             suggestions.append("Significant overhead for magic state distillation. Consider optimizing T-gate count or different distillation protocols.")
    elif results.t_gate_count > 0 and results.circuit_fidelity < 0.95:
        suggestions.append(f"Circuit contains {results.t_gate_count} T-gates with moderate fidelity. Fault-tolerance might be necessary for high precision.")
    
    if results.circuit_depth > 100 and (results.total_gate_count / results.circuit_depth) < (results.circuit_width / 3):
        suggestions.append(f"Circuit is deep ({results.circuit_depth} layers) with potentially low parallelism. Explore techniques to increase gate concurrency or reduce depth.")

    if results.classical_memory_for_simulation_mb is not None and results.classical_memory_for_simulation_mb > 4096:
        suggestions.append(f"State-vector simulation requires significant classical memory (~{results.classical_memory_for_simulation_mb:,.0f} MB). Consider tensor network methods or partial simulation.")

    return suggestions

# --- Main Orchestration Function ---

def estimate_all_quantum_resources(
    circuit: QuantumCircuit,
    architecture: QuantumHardwareArchitecture,
    options: Optional[EstimationOptions] = None
) -> QuantumResourceEstimationResults:
    """
    Performs comprehensive quantum resource estimation.
    """
    if options is None:
        options = EstimationOptions()

    # 1. Basic Circuit Analysis
    logical_depth = calculate_circuit_logical_depth(circuit)
    gate_comp = analyze_gate_composition(circuit)

    # 2. SWAP Overhead and Compiled Depth
    swap_count = estimate_swap_overhead_count(
        circuit, architecture, options.routing_algorithm, options.initial_mapping
    )
    swap_overhead_results = SwapOverheadResults(count=swap_count, algorithm=options.routing_algorithm)
    
    compiled_depth_estimate = logical_depth + math.ceil(swap_count / max(1, circuit.qubits // 2)) if circuit.qubits > 0 else logical_depth

    # 3. Physical Execution Time
    physical_time_ns = estimate_physical_execution_time(
        circuit, architecture, swap_count, compiled_depth_estimate
    )

    # 4. Coherence Analysis
    required_coherence = calculate_required_coherence(physical_time_ns)
    avg_t1 = sum(architecture.t1_times) / len(architecture.t1_times) if isinstance(architecture.t1_times, list) and architecture.t1_times else float(architecture.t1_times)
    avg_t2 = sum(architecture.t2_times) / len(architecture.t2_times) if isinstance(architecture.t2_times, list) and architecture.t2_times else float(architecture.t2_times)
    
    coherence_limited = CoherenceLimitedResults(
        t1=required_coherence.t1 > avg_t1 if avg_t1 > 0 else False,
        t2=required_coherence.t2 > avg_t2 if avg_t2 > 0 else False,
    )

    # 5. Fidelity and Error Rate
    circuit_fidelity = estimate_circuit_fidelity(circuit, architecture, swap_count)
    circuit_error_rate = 1.0 - circuit_fidelity
    # TODO: Implement dominant_error_source heuristic

    # 6. Advanced Metrics
    qv_achievable = estimate_quantum_volume_for_circuit(architecture, circuit.qubits)

    # 7. Classical Resources
    classical_res = estimate_classical_resources(circuit, options.simulation_type)

    # 8. Fault Tolerance
    ft_results: Optional[FaultToleranceResults] = None
    if options.enable_fault_tolerance:
        ft_results = estimate_fault_tolerant_resources(
            logical_qubit_count=circuit.qubits,
            t_gate_count=gate_comp["t_gate_count"],
            logical_circuit_depth=logical_depth, 
            architecture=architecture,
            target_logical_error_rate=options.target_logical_error_rate
        )

    results = QuantumResourceEstimationResults(
        circuit_width=circuit.qubits,
        circuit_depth=logical_depth,
        gate_counts=gate_comp["gate_counts"],
        total_gate_count=gate_comp["total_gate_count"],
        t_gate_count=gate_comp["t_gate_count"],
        clifford_gate_count=gate_comp["clifford_gate_count"],
        non_clifford_gate_count=gate_comp["non_clifford_gate_count"],
        two_qubit_gate_count=gate_comp["two_qubit_gate_count"],
        multi_qubit_gate_count=gate_comp["multi_qubit_gate_count"],
        swap_overhead=swap_overhead_results,
        compiled_circuit_depth=compiled_depth_estimate,
        quantum_volume_achievable=qv_achievable,
        estimated_execution_time_physical=physical_time_ns,
        required_coherence_time=required_coherence,
        coherence_limited=coherence_limited,
        circuit_fidelity=circuit_fidelity,
        circuit_error_rate=circuit_error_rate,
        dominant_error_source=None, # Placeholder
        noise_resilience_score=None, # Placeholder
        classical_preprocessing_complexity=classical_res["complexity"],
        classical_memory_for_simulation_mb=classical_res["memory_mb"],
        fault_tolerance=ft_results,
        analysis_timestamp=__import__('time').time()
    )

    # 9. Optimization Suggestions
    results.optimization_suggestions = generate_optimization_suggestions(results, architecture)
    
    return results

# Example usage (for testing within this file)
if __name__ == "__main__":
    from .circuit import QuantumCircuit, QuantumGate # For standalone run
    from .hardware import QuantumHardwareArchitecture, ConnectivityType # For standalone run
    from .exceptions import OrquestraSDKError # For standalone run

    # Define a simple Bell state circuit
    bell_circuit = QuantumCircuit(
        id="bell_state_py",
        name="Bell State Preparation (Python)",
        qubits=2,
        gates=[
            QuantumGate(type="H", qubits=[0]),
            QuantumGate(type="CNOT", qubits=[0, 1]),
        ]
    )

    # Define a model for a hypothetical hardware architecture
    example_architecture = QuantumHardwareArchitecture(
        name="Hypothetical_NISQ_PyDevice_v1",
        qubit_count=5,
        connectivity=ConnectivityType.LINEAR,
        native_gate_set=["X", "Y", "Z", "H", "CNOT", "RZ"],
        gate_errors={ # Using dict directly
            "single_qubit": 1e-3,
            "two_qubit": 5e-3,
            "H": 1.1e-3, # Specific error for H
            "CNOT": 5.5e-3, # Specific error for CNOT
        },
        readout_errors=[0.01, 0.01, 0.01, 0.01, 0.01], # Per-qubit
        t1_times=[100.0] * 5,      # T1 in microseconds
        t2_times=[80.0] * 5,       # T2 in microseconds
        gate_timings={ # Using dict directly
            "single_qubit": 30.0,   # ns
            "two_qubit": 200.0,     # ns
            "measurement": 500.0,   # ns
            "H": 25.0, # Specific timing for H
        }
    )

    print(f"Estimating for circuit: {bell_circuit.name} on {example_architecture.name}")
    try:
        estimation_options = EstimationOptions(enable_fault_tolerance=True, target_logical_error_rate=1e-9)
        results = estimate_all_quantum_resources(
            circuit=bell_circuit,
            architecture=example_architecture,
            options=estimation_options
        )
        print("\n--- Estimation Results ---")
        print(results.model_dump_json(indent=2)) # Use model_dump_json for Pydantic v2

    except OrquestraSDKError as e:
        print(f"\nSDK Error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
