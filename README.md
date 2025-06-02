# Quantum Orchestra 🎶

**Quantum Orchestra** is a comprehensive platform for quantum resource estimation, simulation management, and provider comparison. It empowers researchers, developers, and organizations to efficiently design, analyze, and deploy quantum algorithms by providing deep insights into resource requirements and optimal execution pathways across various quantum hardware.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

## ✨ Key Features

*   **Intuitive Circuit Design**: Visually build or select pre-defined quantum circuits (Bell Pair, Grover's, QFT).
*   **Advanced Resource Estimation**: In-depth analysis of:
    *   Gate counts, circuit depth, and width.
    *   **Quantum Volume (QV)**, T-gate count, SWAP gate overhead.
    *   Execution time, error rates, and overall circuit fidelity.
    *   Coherence time requirements and limitations.
    *   Classical preprocessing complexity and memory needs.
*   **Fault Tolerance Analysis**: Toggle error correction (e.g., Surface Code) to estimate:
    *   Logical vs. Physical qubit requirements.
    *   Error correction code distance.
    *   Resource state (magic state) overhead.
*   **Multi-Provider Comparison**:
    *   Compare resource needs and estimated costs across major quantum providers (IBM Quantum, Google Quantum AI, Rigetti, IonQ).
    *   Real-time (simulated) provider availability and queue times.
    *   Detailed architecture parameters for each provider.
*   **Customizable & Extensible**: Easily add new quantum circuits, gates, and hardware provider models.
*   **Open Source**: Community-driven development with a transparent roadmap.

## 🚀 Getting Started

Follow these steps to get Quantum Orchestra up and running on your local machine.

### Prerequisites

*   Node.js (v18 or later)
*   npm (v9 or later)
*   Rust (latest stable, for Tauri backend)
*   Git

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/orquestra-ai/orquestra-qre.git quantum-orchestra
    cd quantum-orchestra
    ```

2.  **Install dependencies:**
    This project uses Rust for the backend (via Tauri) and HTML/JavaScript/CSS for the frontend. The `npm install` command installs development tools like the Tauri CLI, which helps in managing the Tauri application.
    ```bash
    # Install Node.js dev dependencies (e.g., @tauri-apps/cli)
    npm install
    ```
    The Rust dependencies will be compiled when you first run the application.

3.  **Run the application:**
    This command compiles the Rust backend and launches the desktop application, serving the frontend directly.
    ```bash
    # Ensure Rust environment is sourced (if you just installed it)
    # source ~/.cargo/env  # Or your shell's equivalent
    npm run tauri:dev
    ```
    The application window should open automatically. If you make changes to the frontend code (HTML, CSS, JS in the `src` directory), they should be reflected upon a refresh or restart of the app. Changes to the Rust backend will require a restart of the `tauri:dev` command.

## 🛠️ Technical Overview: Quantum Resource Estimation

Quantum Orchestra's core is its sophisticated resource estimation engine, found in `src/utils/quantumMetrics.ts`. This engine takes a `QuantumCircuit` definition and a `QuantumArchitecture` model as input and outputs a comprehensive `QuantumResourceEstimation` object.

### Key Metrics Calculated:

*   **Basic Metrics**:
    *   `circuitWidth`: Number of qubits.
    *   `circuitDepth`: Length of the critical path in the circuit.
    *   `gateCount`: Breakdown of gates by type (e.g., H, CNOT, T).
    *   `totalGateCount`: Total number of gates.
*   **Advanced Metrics**:
    *   `quantumVolume`: A holistic benchmark of the quantum computer's capability.
    *   `tGateCount`: Number of T-gates, crucial for fault-tolerant resource estimation.
    *   `swapOverhead`: Estimated number of SWAP gates needed due to limited qubit connectivity.
*   **Time and Coherence**:
    *   `executionTime`: Estimated time to run the circuit on the given architecture (nanoseconds).
    *   `requiredCoherenceTime`: Minimum qubit coherence time needed to run the circuit (microseconds).
    *   `coherenceLimited`: Boolean indicating if the circuit execution is likely limited by qubit coherence times.
*   **Error Analysis**:
    *   `errorRate`: Overall probability of at least one error occurring.
    *   `fidelity`: Overall probability of successful, error-free execution.
    *   `noiseResilienceScore`: A heuristic score (0-1) indicating the circuit's resilience to noise.
*   **Classical Resources**:
    *   `classicalPreprocessingComplexity`: Big O notation for classical computation needed before quantum execution.
    *   `classicalMemoryRequirements`: Estimated classical memory (MB) for simulation or control.
*   **Fault Tolerance (if enabled)**:
    *   `logicalQubitCount`: Number of error-corrected logical qubits.
    *   `physicalQubitCount`: Total physical qubits needed to implement logical qubits using a specified error correction code (e.g., Surface Code).
    *   `errorCorrectionOverhead`: Ratio of physical to logical qubits.
    *   `distanceRequired`: The code distance of the error correction code needed to achieve the target logical error rate.
    *   `resourceStateCount`: Number of magic states (or other resource states) required, often tied to T-gate count.

The engine uses mathematical utilities from `src/utils/mathUtils.ts` for complex number arithmetic and matrix operations, which could be extended for full circuit simulation in the future.

## 🖼️ Feature Highlights

*   **Interactive Circuit Designer**:
    *   Select from sample circuits like Bell Pair, Grover's Algorithm, or Quantum Fourier Transform.
    *   Build custom circuits by adding gates (X, Y, Z, H, CNOT, T, S, Rx, Ry, Rz, SWAP, CZ) to a specified number of qubits.
    *   Visual representation of the circuit (simplified).
    *(Screenshot: A conceptual view of the circuit design panel with qubits as lines and gates as colored blocks on them.)*

*   **Detailed Resource Estimation Panel**:
    *   View basic metrics (gate count, depth, qubits) and advanced metrics (Quantum Volume, T-gate count, SWAP overhead).
    *   Toggle between "Basic" and "Advanced" views for metrics.
    *   See estimated execution time, error rate, and circuit fidelity.
    *   Analyze classical resource requirements and coherence limitations.
    *(Screenshot: The resource estimation section showing cards for Gate Count, Circuit Depth, Required Qubits, Execution Time, Error Rate, and Quantum Volume.)*

*   **Fault Tolerance Analysis**:
    *   A dedicated toggle switch to enable/disable fault tolerance calculations.
    *   When enabled, the panel shows physical qubit requirements, code distance, and resource state counts based on a target logical error rate (e.g., 1e-12 using Surface Code).
    *(Screenshot: The "Fault Tolerance" toggle switch, and when enabled, additional cards for Physical Qubits, Code Distance, and Resource States.)*

*   **Provider Comparison Table**:
    *   Compares estimated cost and execution time across different quantum hardware providers (IBM, Google, Rigetti, IonQ).
    *   Highlights the recommended provider based on a weighted score of cost and time.
    *   Indicates compatibility (sufficient qubits, supported gates).
    *   Shows key architectural details for each provider (qubit count, connectivity, error rates, T1 times, gate times).
    *(Screenshot: A table listing providers, their status (Compatible/Incompatible), estimated cost, execution time, and a "Recommended" badge for the best option.)*

*   **(Conceptual) Real-time Resource Monitor**:
    *   A dashboard to display (simulated) real-time availability of quantum providers.
    *   Track (simulated) active jobs, their progress, and queue positions.
    *   View usage statistics like monthly compute hours and total costs.
    *(Screenshot: A dashboard layout with charts for provider availability, a list of active jobs with progress bars, and summary cards for usage statistics.)*

## 🔌 API Documentation (Quantum Metrics Engine)

The core resource estimation logic is exposed through functions in `src/utils/quantumMetrics.ts`.

### Main Function: `estimateQuantumResources`

```typescript
import { 
  QuantumCircuit, 
  QuantumArchitecture,
  QuantumResourceEstimation,
  estimateQuantumResources 
} from './utils/quantumMetrics';

// Example Usage:
const circuit: QuantumCircuit = { /* ... circuit definition ... */ };
const architecture: QuantumArchitecture = { /* ... hardware model ... */ };
const options = {
  faultTolerant: true,
  targetLogicalErrorRate: 1e-12 // e.g., for high precision
};

const estimationResult: QuantumResourceEstimation = estimateQuantumResources(
  circuit, 
  architecture, 
  options
);

console.log(estimationResult);
```

### Key Data Structures:

*   **`QuantumCircuit`**:
    ```typescript
    interface QuantumCircuit {
      id: string;
      name: string;
      qubits: number;         // Number of qubits in the circuit
      gates: QuantumGate[];   // Array of quantum gates
      depth?: number;         // Optional pre-calculated depth
    }

    interface QuantumGate {
      id: string;
      type: string;           // e.g., 'H', 'CNOT', 'RX'
      qubits: number[];       // Array of qubit indices this gate acts upon
      parameters?: number[];  // Optional parameters (e.g., rotation angle)
      duration?: number;      // Optional gate duration in nanoseconds
      fidelity?: number;      // Optional gate fidelity (0-1)
    }
    ```

*   **`QuantumArchitecture`**:
    ```typescript
    interface QuantumArchitecture {
      name: string;
      qubitCount: number;
      connectivity: ConnectivityType; // 'all-to-all', 'linear', 'grid', 'heavy-hex', etc.
      gateSet: string[];              // List of supported gate types
      gateErrors: Record<string, number>; // Error rate per gate type
      readoutErrors: number[];        // Error rate per qubit for readout
      t1Times: number[];              // T1 relaxation times (microseconds) per qubit
      t2Times: number[];              // T2 dephasing times (microseconds) per qubit
      gateTimings: Record<string, number>; // Duration (nanoseconds) per gate type (e.g., 'single-qubit', 'two-qubit')
    }
    ```

*   **`QuantumResourceEstimation`**: (See "Technical Overview" section for a detailed list of fields).

### Other Utility Functions:

The `quantumMetrics.ts` file also includes various helper functions that can be used independently:

*   `calculateCircuitDepth(circuit: QuantumCircuit): number`
*   `countGatesByType(circuit: QuantumCircuit): Record<string, number>`
*   `calculateQuantumVolume(architecture: QuantumArchitecture, maxCircuitWidth?: number): number`
*   `estimateCircuitFidelity(circuit: QuantumCircuit, architecture: QuantumArchitecture): number`
*   `countTGates(circuit: QuantumCircuit): number`
*   `estimateSwapOverhead(circuit: QuantumCircuit, connectivity: ConnectivityType): number`
*   `calculateRequiredCoherenceTime(circuit: QuantumCircuit, architecture: QuantumArchitecture): number`
*   `analyzeNoiseResilience(circuit: QuantumCircuit): number`
*   `estimateClassicalPreprocessing(circuit: QuantumCircuit): { complexity: string; memoryMB: number }`
*   `calculateLogicalMapping(circuit: QuantumCircuit, targetLogicalErrorRate?: number, physicalErrorRate?: number): { ... }`
*   `estimateResourceStateRequirements(circuit: QuantumCircuit): number`

For mathematical underpinnings (complex numbers, matrices), see `src/utils/mathUtils.ts`.

## 🤝 Contributing

We welcome contributions from everyone! Whether you're fixing a bug, adding a new feature, improving documentation, or suggesting ideas, your help is valuable.

*   **Reporting Issues**: Use the GitHub Issues tab to report bugs or request features. Please provide as much detail as possible.
*   **Code Contributions**:
    1.  Fork the repository.
    2.  Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
    3.  Make your changes and commit them with clear messages.
    4.  Push your branch to your fork (`git push origin feature/your-feature-name`).
    5.  Open a Pull Request against the `main` branch of this repository.
    6.  Ensure your PR passes all CI checks and addresses any review comments.
*   **Contributor License Agreement (CLA)**: For non-trivial contributions, we may require a CLA to ensure the project's open-source integrity. This will be managed via CLA Assistant.

## 🗺️ Roadmap & Future Features

Quantum Orchestra is an evolving project. Here's a glimpse of what we're planning:

### Short-Term (Phase 1 Enhancements)

*   **Plugin Architecture**: Allow easy addition of new estimation models and provider connectors.
*   **Enhanced Circuit Visualization**: More accurate and interactive circuit diagrams.
*   **CLI Tool**: For programmatic resource estimation in CI/CD pipelines.
*   **Public API**: A REST/GraphQL API for accessing estimation capabilities.
*   **More Pre-defined Circuits**: Expand the library of sample quantum algorithms.

### Mid-Term (Potential Phase 2 - Premium/SaaS Features)

*   **Advanced Circuit Optimization**: Algorithms to reduce gate count, depth, or SWAP overhead.
*   **Full Multi-Provider Orchestration**: Manage and submit jobs directly to quantum hardware providers.
*   **Team Workspaces & Collaboration**: Features for research groups and enterprise teams.
*   **Historical Analysis & Reporting**: Track resource usage and costs over time.
*   **Integration with Quantum Compilers**: Connect with tools like Qiskit, Cirq, PennyLane for circuit import/export.

### Long-Term Vision

*   **Machine Learning for Resource Prediction**: Use historical data to improve estimation accuracy.
*   **Support for Hybrid Quantum-Classical Algorithms**: Estimate resources for complex workflows.
*   **Educational Modules**: Interactive tutorials for learning quantum resource estimation.

The community will play a key role in shaping this roadmap. Join our discussions to share your ideas!

## 🧩 How to Add New Quantum Providers

Adding a new quantum hardware provider to Quantum Orchestra is designed to be straightforward.

1.  **Define the `QuantumArchitecture`**:
    Create a new `QuantumArchitecture` object in `src/components/QuantumOrchestra.tsx` (or a dedicated provider configuration file in the future). This object should accurately model the hardware's characteristics:
    ```typescript
    const myNewProviderArchitecture: QuantumArchitecture = {
      name: 'My New Quantum Processor',
      qubitCount: 100,
      connectivity: 'grid', // or 'all-to-all', 'linear', etc.
      gateSet: ['X', 'Y', 'Z', 'H', 'CNOT', /* ... other supported gates ... */],
      gateErrors: {
        'single-qubit': 0.0005, 
        'two-qubit': 0.005,
        /* ... specific gate errors ... */
      },
      readoutErrors: [0.01, /* ... per qubit if available ... */],
      t1Times: [150, /* ... per qubit if available ... */], // in microseconds
      t2Times: [70, /* ... per qubit if available ... */],  // in microseconds
      gateTimings: { 
        'single-qubit': 30, // in nanoseconds
        'two-qubit': 200,
        'readout': 1000
      }
    };
    ```

2.  **Add to `quantumProviders` Array**:
    In `src/components/QuantumOrchestra.tsx`, add a new entry to the `quantumProviders` array:
    ```typescript
    const quantumProviders: QuantumProvider[] = [
      // ... existing providers ...
      {
        id: 'my-new-provider',
        name: 'My New Provider Inc.',
        logo: 'my-new-provider-logo.png', // Add logo to public assets
        architecture: myNewProviderArchitecture, // Reference the architecture object
        costPerHour: 150, // Estimated cost
        queueTime: 40,    // Average queue time in minutes
        availability: 90  // Percentage availability
      }
    ];
    ```

3.  **Test**:
    Run the application and verify that your new provider appears in the comparison table and that resource estimations are calculated correctly for its architecture.

Future versions will likely move provider definitions to a separate configuration system or a plugin model for easier management.

## 📚 Quantum Computing Resources & Papers

To learn more about quantum computing and resource estimation:

### Major Quantum Platforms & SDKs:

*   [IBM Quantum](https://quantum-computing.ibm.com/) & [Qiskit](https://qiskit.org/)
*   [Google Quantum AI](https://quantumai.google/) & [Cirq](https://quantumai.google/cirq)
*   [Rigetti Computing](https://www.rigetti.com/) & [Forest SDK (pyQuil)](https://pyquil-docs.rigetti.com/)
*   [IonQ](https://ionq.com/)
*   [Amazon Braket](https://aws.amazon.com/braket/)
*   [Azure Quantum](https://azure.microsoft.com/en-us/services/quantum/)
*   [PennyLane](https://pennylane.ai/) (Quantum Machine Learning)

### Research & Preprints:

*   [arXiv quantum-ph](https://arxiv.org/abs/quant-ph): The primary repository for quantum physics preprints.

### Key Concepts & General Reading:

*   Nielsen, M. A., & Chuang, I. L. (2010). *Quantum Computation and Quantum Information: 10th Anniversary Edition*. Cambridge University Press. (The "Bible" of quantum computing)
*   Preskill, J. (1998). *Quantum Computation lecture notes*. [Caltech](http://www.theory.caltech.edu/~preskill/ph229/) (Excellent introductory material)
*   Understanding Quantum Volume: [IBM Research Blog](https://research.ibm.com/blog/what-is-quantum-volume)
*   Surface Codes and Fault-Tolerant Quantum Computing: Fowler, A. G., Mariantoni, M., Martinis, J. M., & Cleland, A. N. (2012). Surface codes: Towards practical large-scale quantum computation. *Physical Review A, 86*(3), 032324. ([arXiv:1208.0928](https://arxiv.org/abs/1208.0928))

This list is not exhaustive but provides a good starting point for exploring the field.

## 📜 License

Quantum Orchestra is licensed under the [Apache License, Version 2.0](LICENSE).
You can find a copy of the license in the `LICENSE` file in this repository.

---

We are excited to build the future of quantum resource management with you! Join our community, contribute your expertise, and let's orchestrate the quantum revolution together.
