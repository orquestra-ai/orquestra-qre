/**
 * Quantum Metrics Utility Library
 *
 * This library provides a comprehensive suite of functions for quantum resource estimation,
 * circuit analysis, error modeling, and fault-tolerance calculations. It aims to offer
 * academically rigorous tools for researchers and developers in quantum computing.
 *
 * @module quantumMetrics
 * @see Nielsen, M. A., & Chuang, I. L. (2010). Quantum Computation and Quantum Information. Cambridge University Press.
 * @see Fowler, A. G., Mariantoni, M., Martinis, J. M., & Cleland, A. N. (2012). Surface codes: Towards practical large-scale quantum computation. Physical Review A, 86(3), 032324.
 * @see Bravyi, S., & Kitaev, A. (2005). Universal quantum computation with ideal Clifford gates and noisy ancillas. Physical Review A, 71(2), 022316.
 * @see Cross, A. W., Bishop, L. S., Sheldon, S., Nation, P. D., & Gambetta, J. M. (2019). Validating quantum computers using randomized model circuits. Physical Review A, 100(3), 032328.
 */

import { Complex, Matrix, QuantumGates } from './mathUtils'; // Assuming mathUtils.ts provides these

// ======== Type Definitions ========

/**
 * Represents a quantum gate in a circuit.
 * A gate is defined by its type (e.g., 'H', 'CNOT'), the qubits it acts upon,
 * and optional parameters (e.g., rotation angle).
 */
export interface QuantumGate {
  id: string; // Unique identifier for the gate instance
  type: string; // Gate type, e.g., 'H', 'X', 'CNOT', 'RX'
  qubits: number[]; // Array of qubit indices this gate acts upon (0-indexed)
  parameters?: number[]; // Optional parameters, e.g., angle for rotation gates
  duration?: number; // Optional gate duration in nanoseconds, overrides architecture default
  fidelity?: number; // Optional gate fidelity (0-1), overrides architecture default
}

/**
 * Represents a quantum circuit.
 * A circuit consists of a specified number of qubits and a sequence of quantum gates.
 */
export interface QuantumCircuit {
  id: string; // Unique identifier for the circuit
  name: string; // Human-readable name for the circuit
  qubits: number; // Total number of qubits in the circuit
  gates: QuantumGate[]; // Ordered list of gates in the circuit
  depth?: number; // Optional pre-calculated logical depth
  metadata?: Record<string, any>; // Optional metadata (e.g., description, source)
}

/**
 * Defines the physical characteristics and performance parameters of a quantum hardware architecture.
 * This model is crucial for realistic resource estimation.
 */
export interface QuantumHardwareArchitecture {
  name: string; // Name of the quantum processor or architecture
  qubitCount: number; // Total number of available physical qubits
  connectivity: ConnectivityType; // Qubit interaction topology (e.g., 'all-to-all', 'grid')
  nativeGateSet: string[]; // List of gate types natively supported by the hardware
  gateErrors: Record<string, number>; // Average error rate per native gate type (e.g., {'CNOT': 0.005, 'U3': 0.001})
                                      // Special keys: 'single-qubit' (average for any 1Q gate), 'two-qubit' (average for any 2Q gate)
  readoutErrors: number[]; // Array of readout error rates per qubit, or a single average if uniform
  t1Times: number[]; // Array of T1 relaxation times (in microseconds) per qubit, or a single average
  t2Times: number[]; // Array of T2 dephasing/coherence times (in microseconds) per qubit, or a single average
  gateTimings: Record<string, number>; // Average duration (in nanoseconds) per native gate type
                                       // Special keys: 'single-qubit', 'two-qubit', 'measurement'
  crosstalkMatrix?: number[][]; // Optional matrix describing crosstalk error rates between pairs of qubits
  constraints?: {
    maxCircuitDepth?: number; // Maximum depth supported
    maxShots?: number; // Maximum number of shots per execution
  };
}

/**
 * Types of qubit connectivity patterns found in quantum hardware.
 * - `all-to-all`: Any qubit can interact directly with any other qubit.
 * - `linear`: Qubits are arranged in a line, only nearest neighbors interact.
 * - `ring`: Linear connectivity with wraparound.
 * - `grid`: Qubits arranged in a 2D grid, nearest neighbors interact.
 * - `heavy-hex` / `heavy-square`: Specific lattice structures used by some superconducting devices (e.g., IBM, Rigetti).
 * - `custom`: Connectivity defined by an explicit adjacency list or matrix.
 */
export type ConnectivityType =
  | 'all-to-all'
  | 'linear'
  | 'ring'
  | 'grid'
  | 'heavy-hex'
  | 'heavy-square'
  | { type: 'custom'; adjacencies: number[][] };


/**
 * Comprehensive results of quantum resource estimation.
 * This structure holds all calculated metrics for a given circuit and architecture.
 */
export interface QuantumResourceEstimationResults {
  // Basic Circuit Metrics
  circuitWidth: number; // N_q: Number of qubits used by the circuit
  circuitDepth: number; // D: Number of layers in the circuit (logical depth)
  gateCounts: Record<string, number>; // Breakdown of gate types and their counts
  totalGateCount: number; // Total number of gates in the circuit

  // Advanced Circuit Metrics
  tGateCount: number; // N_T: Number of T-gates (critical for FTQC)
  cliffordGateCount: number; // Number of Clifford gates
  nonCliffordGateCount: number; // Number of non-Clifford gates (T, Tdg, CCZ, etc.)
  twoQubitGateCount: number; // Total number of two-qubit gates
  multiQubitGateCount: number; // Total number of gates acting on >2 qubits

  // Hardware Interaction Metrics
  swapOverhead: { // Estimated SWAP gates needed due to limited connectivity
    count: number; // N_SWAP
    algorithm: 'shortest-path' | 'greedy-router' | 'none';
  };
  compiledCircuitDepth?: number; // D_compiled: Estimated depth after SWAP insertion and compilation
  quantumVolumeAchievable?: number; // QV: Estimated Quantum Volume for this circuit size on this arch

  // Time and Coherence Analysis
  estimatedExecutionTimePhysical: number; // T_exec: Total physical execution time (nanoseconds)
  requiredCoherenceTime: { // Minimum T1/T2 needed
    t1: number; // microseconds
    t2: number; // microseconds
  };
  coherenceLimited: { // Whether execution is likely limited by T1/T2
    t1: boolean;
    t2: boolean;
  };

  // Error and Fidelity Analysis
  circuitFidelity: number; // F_circuit: Probability of error-free execution (0-1)
  circuitErrorRate: number; // ε_circuit = 1 - F_circuit
  dominantErrorSource?: string; // Heuristic: 'gate_errors', 'readout_errors', 'decoherence'
  noiseResilienceScore?: number; // Heuristic score (0-1) of circuit's resilience

  // Classical Resource Analysis
  classicalPreprocessingComplexity?: string; // Big-O notation for classical setup
  classicalMemoryForSimulationMB?: number; // Estimated memory for state-vector simulation
  classicalControlComplexity?: string; // Complexity of classical control systems

  // Fault-Tolerance Analysis (if applicable)
  faultTolerance?: {
    isEnabled: boolean;
    targetLogicalErrorRate: number; // P_L_target
    codeName: string; // e.g., "SurfaceCode"
    codeDistance: number; // d
    logicalQubits: number; // N_L = N_q
    physicalQubitsPerLogical: number; // N_P / N_L
    totalPhysicalQubits: number; // N_P
    errorCorrectionOverheadFactor: number; // (N_P / N_L)
    logicalTimeUnitDuration: number; // Duration of one logical cycle (nanoseconds)
    logicalDepth: number; // D_L: Number of logical time steps
    totalLogicalExecutionTime: number; // T_L_exec (nanoseconds)
    resourceStateCount: number; // Number of magic states (or other resource states)
    distillationOverhead?: number; // Overhead factor for magic state distillation
  };

  // Optimization Suggestions
  optimizationSuggestions?: string[];

  // Timestamp of analysis
  analysisTimestamp: number;
}

// ======== Constants and Benchmarks ========

/**
 * Default physical error rate for qubits if not specified by architecture.
 * Represents a typical error rate for current NISQ devices.
 */
export const DEFAULT_PHYSICAL_ERROR_RATE = 1e-3; // 0.1%

/**
 * Default safety factor for coherence time calculations.
 * Execution time should be `SafetyFactor` times shorter than coherence times.
 */
export const COHERENCE_SAFETY_FACTOR = 5;

/**
 * Parameters for Surface Code fault-tolerance calculations.
 * @see Fowler, A. G. et al. (2012). Surface codes: Towards practical large-scale quantum computation.
 */
export const SURFACE_CODE_PARAMS = {
  THRESHOLD_ERROR_RATE: 1e-2, // P_th: Approximate error threshold for the surface code
  CONSTANT_FACTOR_A: 0.1,    // A: Constant factor in logical error rate formula P_L ~ A * (P_p/P_th)^((d+1)/2)
  // Physical qubits per logical qubit for distance d: d^2 for data + (d-1)^2 for measure = 2d^2 - 2d + 1
  // Or simply 2d^2 for a common rough estimate.
  // More precise: For a standard surface code patch, physical_qubits = 2 * d^2.
  // For data qubits: d^2. For measure qubits: (d^2 - 1). Total: 2d^2 - 1.
  // We use the common 2*d^2 for simplicity in estimation.
  PHYSICAL_PER_LOGICAL_FACTOR_FUNC: (d: number) => 2 * d * d,
  ROUTING_OVERHEAD_FACTOR: 1.5, // Factor to account for routing logical qubits
  LOGICAL_CYCLE_TIME_FACTOR_VS_PHYSICAL_GATE: (d: number) => 5 * d, // Logical cycle time ~ d * physical_gate_time
};

/**
 * Typical gate durations (ns) and error rates for different technologies.
 * Used as fallbacks if architecture details are missing.
 */
export const TECHNOLOGY_BENCHMARKS = {
  superconducting: {
    gateTimings: { 'single-qubit': 30, 'two-qubit': 200, 'measurement': 500 },
    gateErrors: { 'single-qubit': 1e-4, 'two-qubit': 5e-3 },
    readoutErrors: [1e-2],
    t1Times: [100], t2Times: [80], // microseconds
  },
  trapped_ion: {
    gateTimings: { 'single-qubit': 1000, 'two-qubit': 50000, 'measurement': 100000 }, // Slower gates
    gateErrors: { 'single-qubit': 5e-5, 'two-qubit': 1e-3 },
    readoutErrors: [5e-3],
    t1Times: [1e6], t2Times: [1e5], // Much longer coherence
  },
  photonic: { // Highly varied, example values
    gateTimings: { 'single-qubit': 10, 'two-qubit': 100, 'measurement': 1000 }, // Potentially fast, but loss is an issue
    gateErrors: { 'single-qubit': 1e-3, 'two-qubit': 1e-2, 'photon_loss': 0.01 }, // Photon loss is a major error source
    readoutErrors: [2e-2],
    t1Times: [Infinity], t2Times: [Infinity], // Coherence often not the primary limit for photonic qubits
  },
};


// ======== Core Circuit Analysis Functions ========

/**
 * Calculates the logical depth of a quantum circuit.
 * The depth is the minimum number of time steps required to execute the circuit,
 * assuming gates acting on disjoint sets of qubits can be performed in parallel.
 *
 * Algorithm:
 * 1. Initialize `layer_busy_until[q] = 0` for each qubit `q`.
 * 2. For each gate `g` in the circuit:
 *    a. `gate_start_layer = max(layer_busy_until[q_i])` for all qubits `q_i` in `g`.
 *    b. `layer_busy_until[q_i] = gate_start_layer + 1` for all `q_i` in `g`.
 * 3. `circuit_depth = max(layer_busy_until[q])` over all qubits `q`.
 *
 * @param circuit The quantum circuit.
 * @returns The logical circuit depth.
 */
export function calculateCircuitLogicalDepth(circuit: QuantumCircuit): number {
  if (circuit.gates.length === 0) return 0;

  const qubitLayerTracker: number[] = Array(circuit.qubits).fill(0);
  let maxLayer = 0;

  for (const gate of circuit.gates) {
    let currentGateStartLayer = 0;
    for (const qubitIndex of gate.qubits) {
      if (qubitIndex >= circuit.qubits) {
        throw new Error(`Gate ${gate.id} references qubit ${qubitIndex}, but circuit only has ${circuit.qubits} qubits.`);
      }
      currentGateStartLayer = Math.max(currentGateStartLayer, qubitLayerTracker[qubitIndex]);
    }
    for (const qubitIndex of gate.qubits) {
      qubitLayerTracker[qubitIndex] = currentGateStartLayer + 1;
    }
    maxLayer = Math.max(maxLayer, currentGateStartLayer + 1);
  }
  return maxLayer;
}

/**
 * Counts the occurrences of each gate type and other gate categories in the circuit.
 *
 * @param circuit The quantum circuit.
 * @returns An object containing:
 *  - `gateCounts`: Record of counts for each specific gate type (e.g., {'H': 10, 'CNOT': 5}).
 *  - `totalGateCount`: Total number of gates.
 *  - `tGateCount`: Number of T or Tdg gates.
 *  - `cliffordGateCount`: Number of Clifford gates (approximated).
 *  - `nonCliffordGateCount`: Number of non-Clifford gates.
 *  - `twoQubitGateCount`: Number of two-qubit gates.
 *  - `multiQubitGateCount`: Number of gates acting on >2 qubits.
 */
export function analyzeGateComposition(circuit: QuantumCircuit): {
  gateCounts: Record<string, number>;
  totalGateCount: number;
  tGateCount: number;
  cliffordGateCount: number;
  nonCliffordGateCount: number;
  twoQubitGateCount: number;
  multiQubitGateCount: number;
} {
  const gateCounts: Record<string, number> = {};
  let tGateCount = 0;
  let cliffordGateCount = 0;
  let nonCliffordGateCount = 0;
  let twoQubitGateCount = 0;
  let multiQubitGateCount = 0;

  // Common Clifford gates (approximation, as some parameterized gates can be Clifford)
  const CLIFFORD_GATES = new Set(['X', 'Y', 'Z', 'H', 'S', 'SDG', 'CX', 'CY', 'CZ', 'CNOT', 'SWAP']);

  for (const gate of circuit.gates) {
    gateCounts[gate.type] = (gateCounts[gate.type] || 0) + 1;

    if (gate.type === 'T' || gate.type === 'TDG') {
      tGateCount++;
    }

    if (CLIFFORD_GATES.has(gate.type.toUpperCase())) {
      cliffordGateCount++;
    } else {
      nonCliffordGateCount++;
      // T and Tdg are non-Clifford, ensure they are counted here if not in CLIFFORD_GATES set.
      // Typically, universal gate sets are Clifford + T.
    }

    if (gate.qubits.length === 2) {
      twoQubitGateCount++;
    } else if (gate.qubits.length > 2) {
      multiQubitGateCount++;
    }
  }
  // Refine nonClifford if T gates were double counted (if T is not in CLIFFORD_GATES)
  // This depends on the precise definition of CLIFFORD_GATES.
  // For now, assume T/TDG are the primary non-Cliffords we track separately.

  return {
    gateCounts,
    totalGateCount: circuit.gates.length,
    tGateCount,
    cliffordGateCount,
    nonCliffordGateCount, // This will include T-gates if T is not in CLIFFORD_GATES
    twoQubitGateCount,
    multiQubitGateCount,
  };
}

// ======== Advanced Metrics Calculation ========

/**
 * Estimates the Quantum Volume (QV) achievable by a circuit of a given width on a specific architecture.
 * QV = 2^n, where n is the largest integer such that the machine can successfully run random circuits
 * of n qubits and depth n with heavy output probability > 2/3.
 * @see Cross, A. W., et al. (2019). Validating quantum computers using randomized model circuits. Phys. Rev. A, 100(3), 032328.
 *
 * This implementation uses a simplified fidelity-based estimation.
 *
 * @param architecture The quantum hardware architecture.
 * @param circuitWidth The width (number of qubits) of the circuit for which QV is being assessed.
 * @returns Estimated Quantum Volume.
 */
export function estimateQuantumVolumeForCircuit(
  architecture: QuantumHardwareArchitecture,
  circuitWidth: number
): number {
  if (circuitWidth <= 0) return 1; // QV is at least 2^0 = 1
  if (circuitWidth > architecture.qubitCount) circuitWidth = architecture.qubitCount;

  // For a square circuit of width n and depth n:
  // Number of two-qubit gates is roughly n * n / 2 (assuming dense random circuits)
  // Number of single-qubit gates is roughly n * n
  // This is a very rough model. True QV model circuits have specific structures.

  let effectiveN = 0;
  for (let n = 1; n <= circuitWidth; n++) {
    // Create a representative model circuit of size n x n
    // Number of gate "moments" or layers is n.
    // In each layer, assume roughly n/2 two-qubit gates and n single-qubit gates.
    // Total 2Q gates ~ n * (n/2), total 1Q gates ~ n * n.
    // This is a simplification. Actual QV circuits use specific random SU(4) unitaries.

    const numTwoQubitGatesInLayer = Math.floor(n / 2); // Pairs of qubits
    const numSingleQubitGatesInLayer = n;
    
    let layerFidelity = 1.0;

    // Average error rates
    const avgSingleQubitError = architecture.gateErrors['single-qubit'] || architecture.gateErrors['U3'] || DEFAULT_PHYSICAL_ERROR_RATE;
    const avgTwoQubitError = architecture.gateErrors['two-qubit'] || architecture.gateErrors['CNOT'] || architecture.gateErrors['CX'] || (DEFAULT_PHYSICAL_ERROR_RATE * 10);
    
    // Fidelity of one layer of the model circuit
    // F_layer = (F_1q)^N_1q * (F_2q)^N_2q
    const singleQubitFidelityLayer = Math.pow(1 - avgSingleQubitError, numSingleQubitGatesInLayer);
    const twoQubitFidelityLayer = Math.pow(1 - avgTwoQubitError, numTwoQubitGatesInLayer);
    layerFidelity = singleQubitFidelityLayer * twoQubitFidelityLayer;

    // Total circuit fidelity F_circuit = (F_layer)^depth * F_readout
    // For QV, depth = n.
    const circuitFidelityWithoutReadout = Math.pow(layerFidelity, n);
    
    // Readout fidelity (assuming all n qubits are measured)
    const avgReadoutError = Array.isArray(architecture.readoutErrors) && architecture.readoutErrors.length > 0
        ? architecture.readoutErrors.reduce((a, b) => a + b, 0) / architecture.readoutErrors.length
        : (architecture.readoutErrors as unknown as number || (DEFAULT_PHYSICAL_ERROR_RATE * 5)); // Cast if it's a single number
    const readoutFidelity = Math.pow(1 - avgReadoutError, n);

    const totalCircuitFidelity = circuitFidelityWithoutReadout * readoutFidelity;

    // Heavy Output Probability (HOP) > 2/3. Approximated by F_circuit > 2/3.
    if (totalCircuitFidelity > 2/3) {
      effectiveN = n;
    } else {
      break; // Cannot achieve larger square circuits
    }
  }
  return Math.pow(2, effectiveN);
}


/**
 * Estimates SWAP gate overhead required to execute a circuit on hardware with limited connectivity.
 *
 * @param circuit The quantum circuit.
 *   - `circuit.qubits`: Number of logical qubits.
 *   - `circuit.gates`: List of gates, where each gate specifies logical qubits it acts on.
 * @param architecture The quantum hardware architecture.
 *   - `architecture.qubitCount`: Number of physical qubits.
 *   - `architecture.connectivity`: Defines the physical qubit interaction graph.
 * @param routingAlgorithm The routing algorithm to use for SWAP estimation.
 *   - `'shortest-path'`: A naive estimation summing shortest path distances for each 2Q gate. (Lower bound)
 *   - `'greedy-router'`: A simple greedy algorithm that inserts SWAPs iteratively. (More realistic but still heuristic)
 * @param initialMapping Optional initial mapping of logical to physical qubits. If not provided, a default linear mapping is assumed.
 * @returns Estimated number of SWAP gates.
 *
 * @see Li, G., Ding, Y., & Xie, Y. (2019). Tackling the qubit mapping problem for NISQ-era quantum devices. ASPLOS '19. (SABRE algorithm)
 * @see Zulehner, A., Paler, A., & Wille, R. (2018). An efficient methodology for mapping quantum circuits to the IBM QX architectures. IEEE TCAD.
 */
export function estimateSwapOverheadCount(
  circuit: QuantumCircuit,
  architecture: QuantumHardwareArchitecture,
  routingAlgorithm: 'shortest-path' | 'greedy-router' = 'greedy-router',
  initialMapping?: number[] // logical_qubit_idx -> physical_qubit_idx
): number {
  if (architecture.connectivity === 'all-to-all') return 0;

  const numLogicalQubits = circuit.qubits;
  const numPhysicalQubits = architecture.qubitCount;

  if (numLogicalQubits > numPhysicalQubits) {
    // Cannot map, effectively infinite SWAPs or impossible
    return Infinity; 
  }

  // Build connectivity graph for physical qubits
  const adj = buildAdjacencyList(architecture);

  // Initialize mapping: logical qubit i -> physical qubit initialMapping[i] or i
  let currentMapping = initialMapping 
    ? [...initialMapping] 
    : Array.from({ length: numLogicalQubits }, (_, i) => i);
  
  // Validate initial mapping
  if (new Set(currentMapping).size !== numLogicalQubits || currentMapping.some(p => p >= numPhysicalQubits)) {
      console.warn("Invalid initial SWAP mapping provided or default mapping exceeds physical qubits. Resetting to default linear if possible.");
      currentMapping = Array.from({ length: numLogicalQubits }, (_, i) => i);
      if (currentMapping.some(p => p >= numPhysicalQubits)) return Infinity; // Still impossible
  }


  let totalSwaps = 0;

  if (routingAlgorithm === 'shortest-path') {
    for (const gate of circuit.gates) {
      if (gate.qubits.length === 2) {
        const [logQ1, logQ2] = gate.qubits;
        const physQ1 = currentMapping[logQ1];
        const physQ2 = currentMapping[logQ2];

        if (physQ1 === undefined || physQ2 === undefined) continue; // Qubit not in mapping

        const dist = shortestPathDistance(physQ1, physQ2, adj);
        if (dist > 1) {
          totalSwaps += (dist - 1); // Each SWAP reduces distance by at most 1 (in best case)
        }
      }
    }
  } else if (routingAlgorithm === 'greedy-router') {
    // A more stateful, iterative approach
    // This is a simplified greedy router. Real routers are much more complex (e.g., SABRE).
    const activePhysicalQubits = new Set(currentMapping);

    for (const gate of circuit.gates) {
      if (gate.qubits.length === 2) {
        const [logQ1, logQ2] = gate.qubits;
        let physQ1 = currentMapping[logQ1];
        let physQ2 = currentMapping[logQ2];

        if (physQ1 === undefined || physQ2 === undefined) continue;

        // While q1 and q2 are not adjacent
        while (!adj[physQ1]?.includes(physQ2)) {
          // Find a SWAP that brings physQ1 closer to physQ2 or vice-versa
          // Greedy: Find a neighbor of physQ1 (or physQ2) that is on a shorter path to physQ2 (or physQ1)
          // And perform a SWAP with that neighbor.
          // This requires finding a "good" SWAP.
          
          let bestSwap: [number, number] | null = null;
          let currentDist = shortestPathDistance(physQ1, physQ2, adj);
          if (currentDist <= 1) break; // Already adjacent or error

          // Try swapping physQ1 with one of its neighbors
          for (const neighborOfQ1 of adj[physQ1] || []) {
            if (!activePhysicalQubits.has(neighborOfQ1)) continue; // Skip if neighbor is not an active physical qubit
            const distAfterSwap = shortestPathDistance(neighborOfQ1, physQ2, adj);
            if (distAfterSwap < currentDist) {
              bestSwap = [physQ1, neighborOfQ1];
              currentDist = distAfterSwap;
            }
          }
          // Try swapping physQ2 with one of its neighbors
          for (const neighborOfQ2 of adj[physQ2] || []) {
             if (!activePhysicalQubits.has(neighborOfQ2)) continue;
            const distAfterSwap = shortestPathDistance(physQ1, neighborOfQ2, adj);
            if (distAfterSwap < currentDist) {
              bestSwap = [physQ2, neighborOfQ2];
              currentDist = distAfterSwap;
            }
          }

          if (bestSwap) {
            totalSwaps++;
            // Update mapping: find logical qubits at bestSwap[0] and bestSwap[1] and swap them
            const logAtSwap0 = currentMapping.findIndex(p => p === bestSwap![0]);
            const logAtSwap1 = currentMapping.findIndex(p => p === bestSwap![1]);
            
            if (logAtSwap0 !== -1 && logAtSwap1 !== -1) {
                currentMapping[logAtSwap0] = bestSwap![1];
                currentMapping[logAtSwap1] = bestSwap![0];
                // Update physQ1 and physQ2 based on the new mapping for the current gate
                physQ1 = currentMapping[logQ1];
                physQ2 = currentMapping[logQ2];
            } else {
                // This case should ideally not happen if mapping is consistent
                // Potentially a physical qubit involved in SWAP is not in current logical mapping
                // For simplicity, break or handle error. A real router would manage this.
                break; 
            }

          } else {
            // No improving SWAP found, could be stuck or already optimal for this step.
            // This indicates a limitation of the greedy approach.
            // For estimation, we might add a penalty or assume failure if no progress.
            // For now, break if no simple progress.
            totalSwaps += (currentDist > 1 ? (currentDist -1) : 0); // Add remaining shortest path as a rough estimate
            break;
          }
        }
      }
    }
  }
  return totalSwaps;
}

/** Helper: Builds adjacency list from QuantumHardwareArchitecture */
function buildAdjacencyList(architecture: QuantumHardwareArchitecture): number[][] {
  const { qubitCount, connectivity } = architecture;
  const adj: number[][] = Array.from({ length: qubitCount }, () => []);

  if (typeof connectivity === 'object' && connectivity.type === 'custom') {
    return connectivity.adjacencies;
  }

  switch (connectivity) {
    case 'all-to-all':
      for (let i = 0; i < qubitCount; i++) {
        for (let j = i + 1; j < qubitCount; j++) {
          adj[i].push(j);
          adj[j].push(i);
        }
      }
      break;
    case 'linear':
      for (let i = 0; i < qubitCount - 1; i++) {
        adj[i].push(i + 1);
        adj[i + 1].push(i);
      }
      break;
    case 'ring':
      for (let i = 0; i < qubitCount; i++) {
        adj[i].push((i + 1) % qubitCount);
        adj[(i + 1) % qubitCount].push(i);
      }
      break;
    case 'grid':
      const side = Math.ceil(Math.sqrt(qubitCount));
      for (let r = 0; r < side; r++) {
        for (let c = 0; c < side; c++) {
          const idx = r * side + c;
          if (idx >= qubitCount) continue;
          if (c + 1 < side && (idx + 1) < qubitCount) { // Right neighbor
            adj[idx].push(idx + 1);
            adj[idx + 1].push(idx);
          }
          if (r + 1 < side && (idx + side) < qubitCount) { // Down neighbor
            adj[idx].push(idx + side);
            adj[idx + side].push(idx);
          }
        }
      }
      break;
    // Simplified 'heavy-hex' and 'heavy-square' for brevity. Real ones are more complex.
    case 'heavy-hex': // Example: degree 2 and 3 alternating pattern
    case 'heavy-square':
      for (let i = 0; i < qubitCount -1; i++) { // Fallback to linear-like for this example
          adj[i].push(i+1);
          adj[i+1].push(i);
          if (i < qubitCount - 2 && (i%3 === 0)) { // Add some cross-links for higher degree
              adj[i].push(i+2);
              adj[i+2].push(i);
          }
      }
      break;
  }
  // Remove duplicate connections if any were added
  return adj.map(neighbors => [...new Set(neighbors)]);
}

/** Helper: BFS for shortest path distance */
function shortestPathDistance(startNode: number, endNode: number, adj: number[][]): number {
  if (startNode === endNode) return 0;
  if (!adj[startNode] || !adj[endNode]) return Infinity; // Node not in graph

  const queue: [number, number][] = [[startNode, 0]];
  const visited: boolean[] = Array(adj.length).fill(false);
  visited[startNode] = true;

  while (queue.length > 0) {
    const [curr, dist] = queue.shift()!;
    if (curr === endNode) return dist;
    for (const neighbor of adj[curr]) {
      if (!visited[neighbor]) {
        visited[neighbor] = true;
        queue.push([neighbor, dist + 1]);
      }
    }
  }
  return Infinity; // No path
}


// ======== Time, Coherence, and Error Analysis ========

/**
 * Estimates the physical execution time of the circuit on the given architecture.
 * Considers gate durations and SWAP overhead.
 *
 * @param circuit The quantum circuit.
 * @param architecture The quantum hardware architecture.
 * @param swapCount Number of SWAP gates inserted.
 * @param compiledCircuitDepth Optional: depth of the circuit after compilation (including SWAPs).
 *                             If not provided, a sequential sum of gate times is used.
 * @returns Estimated physical execution time in nanoseconds.
 */
export function estimatePhysicalExecutionTime(
  circuit: QuantumCircuit,
  architecture: QuantumHardwareArchitecture,
  swapCount: number,
  compiledCircuitDepth?: number
): number {
  let totalTime = 0;
  const defaultSingleQubitTime = architecture.gateTimings['single-qubit'] || TECHNOLOGY_BENCHMARKS.superconducting.gateTimings['single-qubit'];
  const defaultTwoQubitTime = architecture.gateTimings['two-qubit'] || TECHNOLOGY_BENCHMARKS.superconducting.gateTimings['two-qubit'];
  const defaultMeasurementTime = architecture.gateTimings['measurement'] || TECHNOLOGY_BENCHMARKS.superconducting.gateTimings['measurement'];

  if (compiledCircuitDepth && compiledCircuitDepth > 0) {
    // Estimate based on depth: depth * average_layer_duration
    // Average layer duration can be approximated by the slowest gate in a typical layer (often a 2-qubit gate)
    totalTime = compiledCircuitDepth * defaultTwoQubitTime; // Simplification
  } else {
    // Sequential sum of gate times
    for (const gate of circuit.gates) {
      totalTime += gate.duration || 
                   (gate.qubits.length > 1 
                     ? (architecture.gateTimings[gate.type] || defaultTwoQubitTime)
                     : (architecture.gateTimings[gate.type] || defaultSingleQubitTime));
    }
    const swapDuration = 3 * (architecture.gateTimings['CNOT'] || defaultTwoQubitTime); // SWAP = 3 CNOTs
    totalTime += swapCount * swapDuration;
  }
  
  // Add measurement time for all qubits at the end
  totalTime += circuit.qubits * defaultMeasurementTime;

  return totalTime;
}

/**
 * Calculates required coherence times (T1, T2) for the circuit execution.
 *
 * @param physicalExecutionTimeNs Estimated physical execution time in nanoseconds.
 * @returns Required T1 and T2 in microseconds.
 */
export function calculateRequiredCoherence(physicalExecutionTimeNs: number): { t1: number; t2: number } {
  const requiredTimeUs = (physicalExecutionTimeNs / 1000) * COHERENCE_SAFETY_FACTOR;
  // Typically, T1 requirements are related to total duration, T2 to phase-sensitive operations.
  // For simplicity, we set both to the scaled execution time.
  return { t1: requiredTimeUs, t2: requiredTimeUs };
}

/**
 * Estimates the overall circuit fidelity based on individual gate and readout errors.
 * Assumes errors are independent and applies a simple multiplicative model:
 * F_circuit = Π_i F_gate_i * Π_j F_readout_j
 * where F_k = 1 - ε_k.
 *
 * A more advanced model could consider error propagation or correlated errors.
 *
 * @param circuit The quantum circuit.
 * @param architecture The quantum hardware architecture.
 * @param swapCount Number of SWAP gates inserted.
 * @returns Estimated circuit fidelity (0-1).
 */
export function estimateCircuitFidelity(
  circuit: QuantumCircuit,
  architecture: QuantumHardwareArchitecture,
  swapCount: number
): number {
  let totalFidelity = 1.0;

  const defaultSingleQubitError = architecture.gateErrors['single-qubit'] || DEFAULT_PHYSICAL_ERROR_RATE;
  const defaultTwoQubitError = architecture.gateErrors['two-qubit'] || (DEFAULT_PHYSICAL_ERROR_RATE * 10);
  
  // Gate fidelities
  for (const gate of circuit.gates) {
    const errorRate = gate.fidelity !== undefined ? (1 - gate.fidelity) :
                      (gate.qubits.length > 1
                        ? (architecture.gateErrors[gate.type] || defaultTwoQubitError)
                        : (architecture.gateErrors[gate.type] || defaultSingleQubitError));
    totalFidelity *= (1 - errorRate);
  }

  // SWAP gate fidelities (SWAP = 3 CNOTs)
  const cnotErrorRate = architecture.gateErrors['CNOT'] || architecture.gateErrors['CX'] || defaultTwoQubitError;
  const swapFidelity = Math.pow(1 - cnotErrorRate, 3);
  totalFidelity *= Math.pow(swapFidelity, swapCount);

  // Readout fidelities
  const avgReadoutError = Array.isArray(architecture.readoutErrors) && architecture.readoutErrors.length > 0
    ? architecture.readoutErrors.reduce((a, b) => a + b, 0) / architecture.readoutErrors.length
    : (architecture.readoutErrors as unknown as number || (DEFAULT_PHYSICAL_ERROR_RATE * 5));
  totalFidelity *= Math.pow(1 - avgReadoutError, circuit.qubits);
  
  // Optional: Add a simple global depolarizing error based on execution time vs coherence
  // This is a very heuristic addition for decoherence impact.
  const executionTimeUs = (estimatePhysicalExecutionTime(circuit, architecture, swapCount) / 1000);
  const avgT2TimeUs = Array.isArray(architecture.t2Times) && architecture.t2Times.length > 0
    ? architecture.t2Times.reduce((a,b) => a+b,0) / architecture.t2Times.length
    : TECHNOLOGY_BENCHMARKS.superconducting.t2Times[0];
  
  if (avgT2TimeUs > 0) {
      const decoherenceFactor = Math.exp(-executionTimeUs / avgT2TimeUs);
      totalFidelity *= decoherenceFactor;
  }

  return Math.max(0, totalFidelity);
}

// ======== Fault-Tolerance Analysis ========

/**
 * Calculates fault-tolerant resource requirements using the Surface Code model.
 *
 * @param logicalQubitCount N_L: Number of logical qubits (typically circuit.qubits).
 * @param tGateCount N_T: Number of T-gates in the logical circuit.
 * @param logicalCircuitDepth D_L: Depth of the logical circuit.
 * @param architecture The quantum hardware architecture (for physical error rates).
 * @param targetLogicalErrorRate P_L_target: Desired error rate per logical qubit per logical gate cycle.
 * @returns Estimated fault-tolerant resources.
 *
 * @see Fowler, A. G., et al. (2012). Surface codes: Towards practical large-scale quantum computation. PRA 86, 032324.
 * @see Gidney, C., & Ekerå, M. (2021). How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits. Quantum, 5, 433. (For large-scale FT estimates)
 */
export function estimateFaultTolerantResources(
  logicalQubitCount: number,
  tGateCount: number,
  logicalCircuitDepth: number, // Depth in terms of logical gate operations
  architecture: QuantumHardwareArchitecture,
  targetLogicalErrorRate: number = 1e-15
): NonNullable<QuantumResourceEstimationResults['faultTolerance']> {
  const physicalErrorRate = architecture.gateErrors['two-qubit'] || // Use 2Q gate error as dominant physical error
                            architecture.gateErrors['CNOT'] ||
                            DEFAULT_PHYSICAL_ERROR_RATE * 10;

  if (physicalErrorRate >= SURFACE_CODE_PARAMS.THRESHOLD_ERROR_RATE) {
    // Physical error rate is too high for current Surface Code assumptions
    // This indicates FTQC is likely not viable with this physical hardware for this target.
    return {
      isEnabled: true, targetLogicalErrorRate, codeName: "SurfaceCode",
      codeDistance: Infinity, logicalQubits: logicalQubitCount,
      physicalQubitsPerLogical: Infinity, totalPhysicalQubits: Infinity,
      errorCorrectionOverheadFactor: Infinity, logicalTimeUnitDuration: Infinity,
      logicalDepth: logicalCircuitDepth, totalLogicalExecutionTime: Infinity,
      resourceStateCount: Infinity,
      distillationOverhead: Infinity,
    };
  }

  // Estimate code distance 'd' required: P_L_target ≈ A * (P_p / P_th)^((d+1)/2)
  // (d+1)/2 ≈ log_{P_p/P_th} (P_L_target / A)
  // d ≈ 2 * (log(P_L_target / A) / log(P_p / P_th)) - 1
  let d = 2 * (Math.log(targetLogicalErrorRate / SURFACE_CODE_PARAMS.CONSTANT_FACTOR_A) /
               Math.log(physicalErrorRate / SURFACE_CODE_PARAMS.THRESHOLD_ERROR_RATE)) - 1;
  d = Math.ceil(d);
  if (d % 2 === 0) d++; // Distance must be odd
  d = Math.max(3, d); // Minimum distance is 3

  const physicalPerLogical = SURFACE_CODE_PARAMS.PHYSICAL_PER_LOGICAL_FACTOR_FUNC(d);
  const totalPhysicalQubitsRaw = logicalQubitCount * physicalPerLogical;
  // Add overhead for routing, ancillas for magic state distillation, etc.
  const totalPhysicalQubits = Math.ceil(totalPhysicalQubitsRaw * SURFACE_CODE_PARAMS.ROUTING_OVERHEAD_FACTOR);

  // Logical gate cycle time: d * physical_2Q_gate_time
  const physicalTwoQubitGateTime = architecture.gateTimings['two-qubit'] ||
                                   architecture.gateTimings['CNOT'] ||
                                   TECHNOLOGY_BENCHMARKS.superconducting.gateTimings['two-qubit'];
  const logicalTimeUnitDuration = SURFACE_CODE_PARAMS.LOGICAL_CYCLE_TIME_FACTOR_VS_PHYSICAL_GATE(d) * physicalTwoQubitGateTime;

  // Total logical execution time
  const totalLogicalExecutionTime = logicalCircuitDepth * logicalTimeUnitDuration;

  // Magic state (T-state) distillation
  // Number of T-states needed = T-gate count.
  // Distillation adds overhead in terms of physical qubits and time.
  // A 15-to-1 distillation protocol for T-states might use ~100 physical qubits and take ~10*d physical cycles.
  // This is a complex topic. For a rough estimate:
  const resourceStateCount = tGateCount; // Number of magic states needed
  // Distillation overhead can be significant. Assume a factor for physical qubits for distillation.
  // This is a simplification; real estimates involve detailed distillation factory layouts.
  const distillationQubitOverhead = resourceStateCount > 0 ? logicalQubitCount * 0.25 : 0; // Heuristic: 25% more qubits for distillation factories
  
  return {
    isEnabled: true,
    targetLogicalErrorRate,
    codeName: "SurfaceCode",
    codeDistance: d,
    logicalQubits: logicalQubitCount,
    physicalQubitsPerLogical: physicalPerLogical,
    totalPhysicalQubits: totalPhysicalQubits + Math.ceil(distillationQubitOverhead),
    errorCorrectionOverheadFactor: physicalPerLogical * SURFACE_CODE_PARAMS.ROUTING_OVERHEAD_FACTOR,
    logicalTimeUnitDuration,
    logicalDepth: logicalCircuitDepth, // This is the input logical depth
    totalLogicalExecutionTime,
    resourceStateCount,
    distillationOverhead: resourceStateCount > 0 ? 1.25 : 1.0, // Placeholder for overhead factor
  };
}


// ======== Classical Resource Analysis ========

/**
 * Estimates classical computational resources for simulating or controlling the quantum circuit.
 *
 * @param circuit The quantum circuit.
 * @param simulationType Type of classical simulation to estimate for.
 *   - 'state-vector': Full state vector simulation.
 *   - 'tensor-network': Tensor network based simulation (e.g., MPS, PEPS). Complexity varies greatly.
 *   - 'clifford': Simulation of Clifford circuits (efficiently simulable).
 * @returns Estimated classical resources.
 */
export function estimateClassicalResources(
  circuit: QuantumCircuit,
  simulationType: 'state-vector' | 'tensor-network' | 'clifford' = 'state-vector'
): { complexity: string; memoryMB: number } {
  const n = circuit.qubits;
  const g = circuit.gates.length;
  const { cliffordGateCount, totalGateCount } = analyzeGateComposition(circuit);

  if (simulationType === 'clifford') {
    if (cliffordGateCount === totalGateCount) { // Purely Clifford circuit
      // Gottesman-Knill theorem: Clifford circuits can be simulated efficiently.
      // Complexity: O(n*g) or O(n^2 * g) depending on representation. Memory: O(n^2).
      return { complexity: `O(poly(N_q, G_total)) approx O(N_q^2 * G_total)`, memoryMB: Math.ceil((n * n * 8) / (1024 * 1024)) + 1 };
    } else {
      // Mixed circuit, cannot use efficient Clifford simulation directly for full simulation.
      // Fallback to state-vector for non-Clifford parts or treat as state-vector.
      simulationType = 'state-vector';
    }
  }

  if (simulationType === 'state-vector') {
    // Memory: 2^n complex numbers (e.g., 16 bytes per complex double)
    const memoryBytes = Math.pow(2, n) * 16;
    const memoryMB = Math.ceil(memoryBytes / (1024 * 1024));
    // Time complexity: O(g * 2^n) for applying g gates.
    return { complexity: `O(G_total * 2^N_q)`, memoryMB };
  }

  if (simulationType === 'tensor-network') {
    // Highly dependent on circuit structure (e.g., entanglement, treewidth of graph).
    // For low-entanglement 1D circuits (MPS): Memory O(poly(n) * D_max^2), Time O(poly(n) * D_max^3 * g)
    // where D_max is max bond dimension. This is hard to estimate generically.
    return {
      complexity: `Varies (e.g., O(poly(N_q) * D_max^k * G_total) for 1D-like)`,
      memoryMB: NaN, // Cannot give a generic number easily
    };
  }
  
  return { complexity: "Unknown", memoryMB: NaN };
}

// ======== Optimization Suggestions ========

/**
 * Generates optimization suggestions based on resource estimation results.
 *
 * @param results The comprehensive quantum resource estimation results.
 * @param architecture The quantum hardware architecture.
 * @returns An array of textual optimization suggestions.
 */
export function generateOptimizationSuggestions(
  results: QuantumResourceEstimationResults,
  architecture: QuantumHardwareArchitecture
): string[] {
  const suggestions: string[] = [];

  if (results.swapOverhead.count > results.totalGateCount * 0.2) {
    suggestions.push(`High SWAP overhead (${results.swapOverhead.count} SWAPs). Consider circuit re-compilation for the target '${architecture.name}' topology or explore alternative qubit mappings.`);
  }

  if (results.coherenceLimited.t1 || results.coherenceLimited.t2) {
    suggestions.push(`Execution likely coherence-limited. Aim to reduce circuit depth or use hardware with better coherence times. Required T1/T2: ~${results.requiredCoherenceTime.t1.toFixed(1)}µs.`);
  }

  if (results.circuitFidelity < 0.9) {
    suggestions.push(`Low circuit fidelity (${(results.circuitFidelity * 100).toFixed(1)}%). Explore error mitigation techniques or fault-tolerant encoding if high precision is needed.`);
  }
  
  if (results.faultTolerance?.isEnabled) {
    const ft = results.faultTolerance;
    if (ft.totalPhysicalQubits > architecture.qubitCount * 50 && ft.totalPhysicalQubits !== Infinity) { // Arbitrary large factor
        suggestions.push(`Fault-tolerant implementation requires a very large number of physical qubits (${ft.totalPhysicalQubits.toLocaleString()}). Verify algorithm scale or target error rate.`);
    }
    if (ft.tGateCount > 0 && ft.resourceStateCount / ft.tGateCount > 1.5) { // If distillation overhead is high
        suggestions.push(`Significant overhead for magic state distillation. Consider optimizing T-gate count or exploring different distillation protocols.`);
    }
  } else if (results.tGateCount > 0 && results.circuitFidelity < 0.95) {
      suggestions.push(`Circuit contains ${results.tGateCount} T-gates and has moderate fidelity. If high precision is critical, fault-tolerance might be necessary.`);
  }
  
  if (results.circuitDepth > 100 && results.totalGateCount / results.circuitDepth < results.circuitWidth / 3 ) { // Low parallelism for deep circuits
      suggestions.push(`Circuit is deep (${results.circuitDepth} layers) with potentially low parallelism. Explore techniques to increase gate concurrency or reduce depth.`);
  }

  if (results.classicalMemoryForSimulationMB && results.classicalMemoryForSimulationMB > 4096) { // > 4GB
    suggestions.push(`State-vector simulation requires significant classical memory (~${results.classicalMemoryForSimulationMB} MB). Consider tensor network methods or partial simulation for very large circuits.`);
  }

  return suggestions;
}

// ======== Main Orchestration Function ========

/**
 * Performs comprehensive quantum resource estimation for a given circuit and hardware architecture.
 * This is the main entry point function that orchestrates calls to various specialized estimation utilities.
 *
 * @param circuit The quantum circuit to analyze.
 * @param architecture The target quantum hardware architecture.
 * @param options Configuration options for the estimation process.
 *   - `routingAlgorithm`: Algorithm for SWAP overhead estimation.
 *   - `enableFaultTolerance`: Whether to perform fault-tolerance analysis.
 *   - `targetLogicalErrorRate`: Desired logical error rate for FTQC.
 *   - `simulationType`: Type of classical simulation to estimate resources for.
 * @returns A `QuantumResourceEstimationResults` object.
 */
export function estimateAllQuantumResources(
  circuit: QuantumCircuit,
  architecture: QuantumHardwareArchitecture,
  options: {
    routingAlgorithm?: 'shortest-path' | 'greedy-router';
    enableFaultTolerance?: boolean;
    targetLogicalErrorRate?: number;
    simulationType?: 'state-vector' | 'tensor-network' | 'clifford';
  } = {}
): QuantumResourceEstimationResults {
  const {
    routingAlgorithm = 'greedy-router',
    enableFaultTolerance = false,
    targetLogicalErrorRate = 1e-15,
    simulationType = 'state-vector',
  } = options;

  // 1. Basic Circuit Analysis
  const logicalDepth = calculateCircuitLogicalDepth(circuit);
  const gateComposition = analyzeGateComposition(circuit);

  // 2. SWAP Overhead and Compiled Depth
  const swapCount = estimateSwapOverheadCount(circuit, architecture, routingAlgorithm);
  // Estimating compiled depth is complex. For now, add SWAPs to logical depth as a rough guide.
  // Each SWAP layer might add 1 to depth if SWAPs can be parallelized, or more if sequential.
  // A simple model: D_compiled = D_logical + N_SWAP / (N_q / 2) (SWAPs per layer)
  const compiledDepthEstimate = logicalDepth + Math.ceil(swapCount / Math.max(1, Math.floor(circuit.qubits / 2)));


  // 3. Physical Execution Time
  const physicalExecutionTimeNs = estimatePhysicalExecutionTime(circuit, architecture, swapCount, compiledDepthEstimate);

  // 4. Coherence Analysis
  const requiredCoherence = calculateRequiredCoherence(physicalExecutionTimeNs);
  const avgT1 = architecture.t1Times.reduce((s, v) => s + v, 0) / architecture.t1Times.length;
  const avgT2 = architecture.t2Times.reduce((s, v) => s + v, 0) / architecture.t2Times.length;
  const coherenceLimited = {
    t1: requiredCoherence.t1 > avgT1,
    t2: requiredCoherence.t2 > avgT2,
  };

  // 5. Fidelity and Error Rate
  const circuitFidelity = estimateCircuitFidelity(circuit, architecture, swapCount);
  const circuitErrorRate = 1 - circuitFidelity;
  // Dominant error source heuristic (simplified)
  let dominantErrorSource = 'gate_errors';
  // (A more complex model would compare contributions from gate errors, readout, decoherence)


  // 6. Advanced Metrics
  const qvAchievable = estimateQuantumVolumeForCircuit(architecture, circuit.qubits);

  // 7. Classical Resources
  const classicalResources = estimateClassicalResources(circuit, simulationType);

  // 8. Fault Tolerance (if enabled)
  let ftResults: QuantumResourceEstimationResults['faultTolerance'] | undefined = undefined;
  if (enableFaultTolerance) {
    ftResults = estimateFaultTolerantResources(
      circuit.qubits,
      gateComposition.tGateCount,
      logicalDepth, // Using logical depth of the original circuit as input for FT logical depth
      architecture,
      targetLogicalErrorRate
    );
  }
  
  const estimationResults: QuantumResourceEstimationResults = {
    circuitWidth: circuit.qubits,
    circuitDepth: logicalDepth,
    gateCounts: gateComposition.gateCounts,
    totalGateCount: gateComposition.totalGateCount,
    tGateCount: gateComposition.tGateCount,
    cliffordGateCount: gateComposition.cliffordGateCount,
    nonCliffordGateCount: gateComposition.nonCliffordGateCount,
    twoQubitGateCount: gateComposition.twoQubitGateCount,
    multiQubitGateCount: gateComposition.multiQubitGateCount,
    swapOverhead: { count: swapCount, algorithm: routingAlgorithm },
    compiledCircuitDepth: compiledDepthEstimate,
    quantumVolumeAchievable: qvAchievable,
    estimatedExecutionTimePhysical: physicalExecutionTimeNs,
    requiredCoherenceTime: requiredCoherence,
    coherenceLimited,
    circuitFidelity,
    circuitErrorRate,
    dominantErrorSource, // Could be refined
    // noiseResilienceScore: // TODO: Implement a more meaningful score
    classicalPreprocessingComplexity: classicalResources.complexity,
    classicalMemoryForSimulationMB: classicalResources.memoryMB,
    faultTolerance: ftResults,
    analysisTimestamp: Date.now(),
  };

  // 9. Optimization Suggestions
  estimationResults.optimizationSuggestions = generateOptimizationSuggestions(estimationResults, architecture);

  return estimationResults;
}
