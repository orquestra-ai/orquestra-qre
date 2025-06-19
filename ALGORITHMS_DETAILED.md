# Orquestra: Detailed Algorithmic Analysis

This document provides a detailed analysis of the core algorithms implemented within the Orquestra framework for quantum resource estimation. It is intended to supplement the main conceptual paper by offering an in-depth look at the mathematical underpinnings, implementation strategies, and complexity analyses of these algorithms.

## Table of Contents
1.  [Circuit Depth Calculation](#1-circuit-depth-calculation)
2.  [SWAP Overhead Estimation Algorithms](#2-swap-overhead-estimation-algorithms)
    *   [2.1 Shortest-Path Based Estimation](#21-shortest-path-based-estimation)
    *   [2.2 Greedy Routing Based Estimation](#22-greedy-routing-based-estimation)
3.  [Quantum Volume (QV) Estimation Methodology](#3-quantum-volume-qv-estimation-methodology)
4.  [Fault-Tolerance Calculations (Surface Code)](#4-fault-tolerance-calculations-surface-code)
    *   [4.1 Code Distance Estimation](#41-code-distance-estimation)
    *   [4.2 Physical Qubit Overhead](#42-physical-qubit-overhead)
    *   [4.3 Logical Gate Time and T-Factory Overheads](#43-logical-gate-time-and-t-factory-overheads)
5.  [Error Propagation Models and Fidelity Estimation](#5-error-propagation-models-and-fidelity-estimation)
6.  [Classical Simulation Complexity Analysis](#6-classical-simulation-complexity-analysis)
7.  [Coherence Analysis Algorithms](#7-coherence-analysis-algorithms)
8.  [Performance Optimization Techniques (Conceptual Overview)](#8-performance-optimization-techniques-conceptual-overview)
9.  [Benchmarking Methodologies](#9-benchmarking-methodologies)
10. [Validation Strategies](#10-validation-strategies)
11. [References](#11-references)

---

## 1. Circuit Depth Calculation

The logical depth of a quantum circuit, $D$, is a crucial metric representing the minimum number of parallel time steps required to execute all gates in the circuit. It assumes that gates acting on disjoint sets of qubits can be performed concurrently.

### Algorithm: Layer-by-Layer Scheduling
Orquestra employs a standard greedy scheduling algorithm to determine circuit depth.
1.  Initialize an array `qubit_finish_layer[q] = 0` for each qubit $q \in [0, N_q-1]$, where $N_q$ is the total number of qubits in the circuit. This array tracks the layer at which each qubit becomes free.
2.  Initialize `circuit_depth = 0`.
3.  Iterate through each gate $g$ in the circuit's gate list (assuming a topologically valid order or processing sequentially):
    a.  Let $Q_g$ be the set of qubits upon which gate $g$ acts.
    b.  Determine the earliest layer $L_{start}(g)$ at which gate $g$ can begin:
        $L_{start}(g) = \max_{q \in Q_g} \{ \text{qubit\_finish\_layer}[q] \}$
    c.  The gate $g$ is scheduled to execute in layer $L_{start}(g)$. For logical depth calculation, each gate is assumed to take one layer. Thus, it finishes at layer $L_{finish}(g) = L_{start}(g) + 1$.
    d.  Update the finish times for all qubits involved in gate $g$:
        For each $q \in Q_g$, set $\text{qubit\_finish\_layer}[q] = L_{finish}(g)$.
    e.  Update the overall circuit depth:
        $\text{circuit\_depth} = \max(\text{circuit\_depth}, L_{finish}(g))$.
4.  The final value of `circuit_depth` is the logical depth of the circuit.

### Pseudocode:
```plaintext
function CalculateLogicalDepth(circuit):
  N_q = circuit.num_qubits
  qubit_finish_layer = array of size N_q, initialized to 0
  circuit_depth = 0

  for each gate g in circuit.gates:
    gate_start_layer = 0
    for each qubit_idx in g.qubits:
      gate_start_layer = max(gate_start_layer, qubit_finish_layer[qubit_idx])
    
    gate_finish_layer = gate_start_layer + 1
    
    for each qubit_idx in g.qubits:
      qubit_finish_layer[qubit_idx] = gate_finish_layer
      
    circuit_depth = max(circuit_depth, gate_finish_layer)
    
  return circuit_depth
```

### Complexity Analysis:
*   **Time Complexity**: If $G$ is the number of gates and $k_{max}$ is the maximum number of qubits a single gate acts upon (typically 1 or 2 for common gates), iterating through qubits for each gate takes $O(k_{max})$. Thus, the overall time complexity is $O(G \cdot k_{max})$. For circuits with only single- and two-qubit gates, this is $O(G)$.
*   **Space Complexity**: $O(N_q)$ to store `qubit_finish_layer`.

This algorithm provides the *logical depth*. The *physical depth* on actual hardware would further depend on gate execution times, qubit coherence, and specific hardware constraints, which are considered in the physical execution time estimation.

---

## 2. SWAP Overhead Estimation Algorithms

Limited qubit connectivity in most NISQ devices necessitates SWAP operations to enable two-qubit gates between non-adjacent qubits. Orquestra implements two primary strategies for estimating this overhead.

Let $G_L = (V_L, E_L)$ be the logical circuit's interaction graph and $G_P = (V_P, E_P)$ be the physical hardware connectivity graph. A mapping $M: V_L \rightarrow V_P$ assigns logical qubits to physical qubits.

### 2.1 Shortest-Path Based Estimation

This method provides a lower-bound estimate on the number of SWAPs.
1.  **Assumption**: The initial mapping $M$ of logical to physical qubits remains static, or an average/worst-case mapping is considered.
2.  For each two-qubit gate $g(q_a, q_b)$ in the logical circuit:
    a.  Identify the physical qubits $p_a = M(q_a)$ and $p_b = M(q_b)$.
    b.  Compute the shortest path distance $d(p_a, p_b)$ in the physical graph $G_P$ using Breadth-First Search (BFS).
    c.  If $d(p_a, p_b) > 1$, at least $d(p_a, p_b) - 1$ SWAP operations are required to bring $q_a$ and $q_b$ to adjacent physical locations.
3.  The total SWAP overhead is $\sum_{g} (d(M(q_a), M(q_b)) - 1)$ for all two-qubit gates $g$ where $d > 1$.

### Pseudocode (Shortest-Path SWAP Estimation):
```plaintext
function EstimateSwapsShortestPath(circuit, physical_graph, initial_mapping):
  total_swaps = 0
  current_mapping = initial_mapping // logical_idx -> physical_idx

  for each gate g in circuit.gates:
    if g is a two-qubit gate acting on (log_q1, log_q2):
      phys_q1 = current_mapping[log_q1]
      phys_q2 = current_mapping[log_q2]
      
      distance = BFS_ShortestPath(physical_graph, phys_q1, phys_q2)
      
      if distance > 1:
        total_swaps += (distance - 1)
        
  return total_swaps

function BFS_ShortestPath(graph, start_node, end_node):
  // Standard BFS implementation
  // ...
  return path_length or infinity
```

### Complexity Analysis (Shortest-Path):
*   BFS on $G_P=(V_P, E_P)$ takes $O(|V_P| + |E_P|)$ time.
*   If there are $G_{2Q}$ two-qubit gates, the total time complexity is $O(G_{2Q} \cdot (|V_P| + |E_P|))$.
*   Space complexity is $O(|V_P|)$ for BFS and the mapping.

### 2.2 Greedy Routing Based Estimation

This approach attempts a more realistic estimation by simulating a simple routing process.
1.  Initialize `current_mapping` $M: V_L \rightarrow V_P$.
2.  Initialize `total_swaps = 0`.
3.  For each two-qubit gate $g(q_a, q_b)$ in the logical circuit:
    a.  Let $p_a = M(q_a)$ and $p_b = M(q_b)$.
    b.  **While** $p_a$ and $p_b$ are not adjacent in $G_P$:
        i.  Identify a "best" SWAP operation. A common greedy heuristic is to find a physical qubit $p_x$ adjacent to $p_a$ (or $p_b$) such that swapping $M(q_a)$ with $M(q_x)$ (the logical qubit at $p_x$) reduces the distance $d(M(q_a), M(q_b))$ or moves $M(q_a)$ along a shortest path towards $M(q_b)$.
        ii. If such a SWAP $(p_a, p_x)$ is found:
            Increment `total_swaps`.
            Update the mapping $M$: $M(q_a) \leftrightarrow M(q_x)$.
            Update $p_a = M(q_a)$.
        iii.If no beneficial SWAP is found (e.g., local optimum or complex entanglement), this simple greedy router might terminate or apply a penalty. For estimation, one might add the remaining shortest path distance as SWAPs.
4.  Return `total_swaps`.

### Pseudocode (Greedy Router SWAP Estimation - Simplified):
```plaintext
function EstimateSwapsGreedyRouter(circuit, physical_graph, initial_mapping):
  total_swaps = 0
  current_mapping = initial_mapping // logical_idx -> physical_idx
  active_physical_qubits = set of values in current_mapping

  for each gate g in circuit.gates:
    if g is a two-qubit gate acting on (log_q1, log_q2):
      phys_q1 = current_mapping[log_q1]
      phys_q2 = current_mapping[log_q2]
      
      while not AreAdjacent(physical_graph, phys_q1, phys_q2):
        current_distance = BFS_ShortestPath(physical_graph, phys_q1, phys_q2)
        if current_distance <= 1: break // Already adjacent or error
        
        best_swap_candidate = null
        min_new_distance = current_distance
        
        // Try swapping phys_q1 with its neighbors
        for each neighbor_of_q1 in physical_graph.neighbors(phys_q1):
          if neighbor_of_q1 is in active_physical_qubits:
            dist_after_swap = BFS_ShortestPath(physical_graph, neighbor_of_q1, phys_q2)
            if dist_after_swap < min_new_distance:
              min_new_distance = dist_after_swap
              best_swap_candidate = (phys_q1, neighbor_of_q1)
              
        // Try swapping phys_q2 with its neighbors (similar logic)
        // ...

        if best_swap_candidate is not null:
          total_swaps += 1
          swapped_phys_a, swapped_phys_b = best_swap_candidate
          
          log_at_swapped_a = find_logical_qubit(current_mapping, swapped_phys_a)
          log_at_swapped_b = find_logical_qubit(current_mapping, swapped_phys_b)
          
          // Update mapping
          current_mapping[log_at_swapped_a] = swapped_phys_b
          current_mapping[log_at_swapped_b] = swapped_phys_a
          
          // Update current physical qubits for the gate
          phys_q1 = current_mapping[log_q1]
          phys_q2 = current_mapping[log_q2]
        else:
          // No beneficial greedy SWAP found, add remaining distance as estimate
          total_swaps += (current_distance - 1) if current_distance > 1 else 0
          break // End SWAP attempts for this gate
          
  return total_swaps
```

### Complexity Analysis (Greedy Router):
*   The `while` loop can iterate up to $O(|V_P|)$ times per gate in the worst case.
*   Inside the loop, finding the `best_swap_candidate` involves checking neighbors (degree $d_{max}$) and running BFS ($O(|V_P| + |E_P|)$).
*   Total complexity can be roughly $O(G_{2Q} \cdot |V_P| \cdot d_{max} \cdot (|V_P| + |E_P|))$, which is significantly higher than the shortest-path method.
*   More sophisticated routing algorithms like SABRE [Li et al., 2019] use lookaheads and cost functions to achieve better routing with manageable complexity.

---

## 3. Quantum Volume (QV) Estimation Methodology

Quantum Volume (QV) measures the largest square-shaped random circuit ($n \times n$) that a quantum computer can reliably execute. Reliability is defined as achieving a heavy output probability greater than 2/3.

### Methodology in Orquestra:
Orquestra uses a simplified fidelity-based proxy for QV estimation, as direct heavy output probability calculation requires full simulation.
1.  **Model Circuit Generation**: For a given width $n$ (number of qubits), a model circuit of depth $n$ is considered. This circuit consists of $n$ layers. Each layer typically applies random SU(4) unitaries (or a universal gate set approximation) to pairs of qubits, chosen to ensure sufficient entanglement and complexity.
    *   The `estimateQuantumVolumeForCircuit` function in `quantumMetrics.ts` models this by assuming each layer has $\lfloor n/2 \rfloor$ two-qubit gates and $n$ single-qubit gates.
2.  **Fidelity Estimation of Model Circuit**:
    a.  Let $F_{1q}$ and $F_{2q}$ be the average single-qubit and two-qubit gate fidelities derived from `architecture.gateErrors`.
        $F_{1q} = 1 - \epsilon_{1q}$, $F_{2q} = 1 - \epsilon_{2q}$.
    b.  The fidelity of one layer of the model circuit ($L_n$) is estimated as:
        $F_{layer} \approx (F_{1q})^{N_{1q,layer}} \cdot (F_{2q})^{N_{2q,layer}}$
        where $N_{1q,layer} \approx n$ and $N_{2q,layer} \approx \lfloor n/2 \rfloor$.
    c.  The total circuit fidelity before measurement is:
        $F_{circuit,gates} = (F_{layer})^n$ (since depth is $n$).
    d.  Readout fidelity: Let $F_{ro}$ be the average single-qubit readout fidelity ($1 - \epsilon_{ro}$). For $n$ qubits:
        $F_{circuit,readout} = (F_{ro})^n$.
    e.  Total model circuit fidelity:
        $F_{model}(n) = F_{circuit,gates} \cdot F_{circuit,readout}$.
3.  **Success Criterion**: The model circuit of size $n$ is considered "successfully executable" if $F_{model}(n) > 2/3$. This is an approximation of the heavy output probability criterion.
4.  **Iterative Search**:
    Iterate $n$ from 1 up to `architecture.qubitCount`. The largest $n$ for which $F_{model}(n) > 2/3$ is $n_{max}$.
5.  **Quantum Volume**: QV = $2^{n_{max}}$.

### Mathematical Derivation (Simplified Fidelity Model):
The core assumption is that the probability of obtaining a heavy output is strongly correlated with the overall circuit fidelity.
Let $\epsilon_{avg,layer}$ be the average error probability per layer. Then $F_{layer} = 1 - \epsilon_{avg,layer}$.
$F_{model}(n) = (1 - \epsilon_{avg,layer})^n \cdot (1 - \epsilon_{ro})^n$.
We seek the largest $n$ such that this value exceeds $2/3$.

### Complexity Analysis:
*   The loop runs up to $N_q = \text{architecture.qubitCount}$ times.
*   Inside the loop, calculations are $O(1)$.
*   Total time complexity: $O(N_q)$.

### Limitations:
This is a simplified model. Rigorous QV calculation involves:
*   Specific classes of random circuits (e.g., Haar-random SU(4) unitaries).
*   Actual simulation or experimental execution to determine heavy outputs.
*   Statistical analysis over many random circuit instances.
The Orquestra model provides a quick heuristic based on architectural fidelity parameters.

---

## 4. Fault-Tolerance Calculations (Surface Code)

Orquestra QRE provides a detailed estimation of resource overhead when applying fault-tolerant quantum computation using Surface Code and other error correction methods.

### 4.1 Code Distance Estimation

For a desired logical error rate $\epsilon_L$ and given physical error rate $\epsilon_P$, the required code distance $d$ in the Surface Code is estimated as:

$$d = \left\lceil \frac{\ln(\epsilon_L/C)}{\ln(\epsilon_P/\epsilon_0)} \right\rceil$$

Where:
- $\epsilon_0$ is the threshold error rate (typically $\approx 1\%$ for Surface Code)
- $C$ is a constant ($\approx 0.1$)

### 4.2 Physical Qubit Overhead

The Surface Code has a physical-to-logical qubit ratio that scales quadratically with the code distance:

$$n_{physical} = \alpha \cdot d^2 \cdot n_{logical}$$

Where:
- $\alpha$ is a constant factor usually between 1 and 2, depending on the specific Surface Code implementation
- $d$ is the code distance
- $n_{logical}$ is the number of logical qubits in the circuit

In the Orquestra QRE implementation, we use empirical models resulting in approximately 20x overhead for Surface Code and 5x for Repetition Code:

```python
# Error Correction Models in Orquestra QRE
ERROR_CORRECTION_CODES = {
    "None": {"overhead": 1, "logical_to_physical": lambda n: n},
    "Surface Code": {"overhead": 20, "logical_to_physical": lambda n: n * 20},
    "Repetition Code": {"overhead": 5, "logical_to_physical": lambda n: n * 5}
}
```

### 4.3 Timing Overhead with Error Correction

For a quantum circuit with error correction, the runtime is adjusted by an overhead factor:

$$T_{EC} = \gamma \cdot T_{original}$$

Where:
- $\gamma$ is the time overhead factor, typically between 10-100x depending on the error correction code
- $T_{original}$ is the original runtime without error correction

Similarly, the expected fidelity is affected exponentially:

$$F_{EC} = {F_{original}}^{\gamma}$$

## 5. Hardware Provider Models

Orquestra QRE includes detailed models of major quantum computing providers to enable realistic resource estimation:

### 5.1 Hardware Parameter Model

Each hardware provider is modeled using the following parameters:

```python
@dataclass
class HardwareProvider:
    name: str                # Provider name
    max_qubits: int          # Maximum available qubits
    coherence_time_us: float # Coherence time in microseconds
    single_qubit_error: float # Single-qubit gate error rate
    two_qubit_error: float   # Two-qubit gate error rate
    connectivity: str        # Qubit connectivity topology
```

### 5.2 Provider-Specific Parameters

The platform includes empirical models for major quantum hardware providers:

| Provider | Qubits | Coherence Time (μs) | 1Q Error | 2Q Error | Connectivity |
|----------|--------|---------------------|----------|----------|-------------|
| IBM      | 127    | 100                 | 1e-3     | 1e-2     | Heavy Hex   |
| Google   | 72     | 150                 | 5e-4     | 1e-2     | Sycamore    |
| IonQ     | 32     | 1000                | 1e-4     | 2e-3     | All-to-All  |
| Rigetti  | 80     | 80                  | 2e-3     | 1.5e-2   | Lattice     |
| Custom   | 1000   | 10000               | 1e-5     | 1e-4     | Custom      |

### 5.3 Hardware-Aware Estimation Algorithm

Resource estimates are adjusted based on hardware constraints using the following algorithm:

1. Calculate logical resource needs (gates, depth, runtime)
2. If error correction is enabled, calculate physical qubit requirements
3. Check if the circuit exceeds hardware limitations:
   - Physical qubits > max_qubits → Infeasible
   - Estimated runtime > coherence_time → Decoherence likely
4. Adjust fidelity estimates based on hardware error rates
5. For non-fully-connected architectures, estimate SWAP overhead based on connectivity constraints

