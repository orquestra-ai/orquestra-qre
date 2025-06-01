import React, { useState, useEffect } from 'react';
import { 
  CirclePlus, 
  BarChart3, 
  Cpu, 
  DollarSign, 
  RefreshCw, 
  Zap, 
  Settings, 
  ChevronDown, 
  Check, 
  Info,
  AlertTriangle,
  Clock,
  Layers,
  Shield,
  Maximize,
  ToggleRight,
  ToggleLeft,
  HelpCircle
} from 'lucide-react';

// Import the quantum metrics utilities
import { 
  QuantumCircuit, 
  QuantumGate,
  QuantumArchitecture,
  ConnectivityType,
  QuantumResourceEstimation,
  calculateCircuitDepth,
  countGatesByType,
  estimateQuantumResources,
  calculateLogicalMapping
} from '../utils/quantumMetrics';

// Types for resource estimation and providers
interface ResourceEstimation extends QuantumResourceEstimation {
  // Additional UI-specific fields can be added here
  analysisTimestamp: number;
}

interface QuantumProvider {
  id: string;
  name: string;
  logo: string;
  architecture: QuantumArchitecture;
  costPerHour: number;
  queueTime: number; // in minutes
  availability: number; // percentage
}

interface ProviderEstimation {
  providerId: string;
  providerName: string;
  estimatedCost: number;
  estimatedTime: number;
  success: boolean;
  errorMessage?: string;
  recommended: boolean;
  resourceEstimation?: ResourceEstimation;
}

// Define quantum architectures for each provider
const quantumArchitectures: Record<string, QuantumArchitecture> = {
  ibm: {
    name: 'IBM Eagle',
    qubitCount: 127,
    connectivity: 'heavy-hex',
    gateSet: ['X', 'Y', 'Z', 'H', 'CNOT', 'T', 'S', 'Rx', 'Ry', 'Rz'],
    gateErrors: {
      'single-qubit': 0.0001,
      'two-qubit': 0.001,
      'X': 0.0001,
      'Y': 0.0001,
      'Z': 0.0001,
      'H': 0.0002,
      'CNOT': 0.001,
      'T': 0.0002,
      'S': 0.0001,
      'Rx': 0.0002,
      'Ry': 0.0002,
      'Rz': 0.0001
    },
    readoutErrors: [0.01],
    t1Times: [100], // microseconds
    t2Times: [50],  // microseconds
    gateTimings: {
      'single-qubit': 50,  // nanoseconds
      'two-qubit': 300,    // nanoseconds
      'readout': 1000      // nanoseconds
    }
  },
  google: {
    name: 'Google Sycamore',
    qubitCount: 72,
    connectivity: 'grid',
    gateSet: ['X', 'Y', 'Z', 'H', 'CNOT', 'T', 'S', 'Rx', 'Ry', 'Rz', 'iSWAP'],
    gateErrors: {
      'single-qubit': 0.00007,
      'two-qubit': 0.0007,
      'X': 0.00007,
      'Y': 0.00007,
      'Z': 0.00007,
      'H': 0.0001,
      'CNOT': 0.0007,
      'T': 0.0001,
      'S': 0.00007,
      'Rx': 0.0001,
      'Ry': 0.0001,
      'Rz': 0.00007,
      'iSWAP': 0.0007
    },
    readoutErrors: [0.008],
    t1Times: [120], // microseconds
    t2Times: [70],  // microseconds
    gateTimings: {
      'single-qubit': 25,  // nanoseconds
      'two-qubit': 250,    // nanoseconds
      'readout': 800       // nanoseconds
    }
  },
  rigetti: {
    name: 'Rigetti Aspen-M',
    qubitCount: 80,
    connectivity: 'heavy-square',
    gateSet: ['X', 'Y', 'Z', 'H', 'CNOT', 'T', 'S', 'Rx', 'Ry', 'Rz', 'CZ'],
    gateErrors: {
      'single-qubit': 0.00015,
      'two-qubit': 0.0015,
      'X': 0.00015,
      'Y': 0.00015,
      'Z': 0.00015,
      'H': 0.0002,
      'CNOT': 0.0015,
      'T': 0.0002,
      'S': 0.00015,
      'Rx': 0.0002,
      'Ry': 0.0002,
      'Rz': 0.00015,
      'CZ': 0.0015
    },
    readoutErrors: [0.015],
    t1Times: [80], // microseconds
    t2Times: [40], // microseconds
    gateTimings: {
      'single-qubit': 60,  // nanoseconds
      'two-qubit': 350,    // nanoseconds
      'readout': 1200      // nanoseconds
    }
  },
  ionq: {
    name: 'IonQ Harmony',
    qubitCount: 32,
    connectivity: 'all-to-all',
    gateSet: ['X', 'Y', 'Z', 'H', 'CNOT', 'T', 'S', 'Rx', 'Ry', 'Rz', 'MS'],
    gateErrors: {
      'single-qubit': 0.00005,
      'two-qubit': 0.0005,
      'X': 0.00005,
      'Y': 0.00005,
      'Z': 0.00005,
      'H': 0.0001,
      'CNOT': 0.0005,
      'T': 0.0001,
      'S': 0.00005,
      'Rx': 0.0001,
      'Ry': 0.0001,
      'Rz': 0.00005,
      'MS': 0.0005
    },
    readoutErrors: [0.005],
    t1Times: [10000], // microseconds (much longer for trapped ions)
    t2Times: [1000],  // microseconds
    gateTimings: {
      'single-qubit': 1000,  // nanoseconds (slower gates for trapped ions)
      'two-qubit': 2000,     // nanoseconds
      'readout': 10000       // nanoseconds
    }
  }
};

// Mock data for quantum providers
const quantumProviders: QuantumProvider[] = [
  {
    id: 'ibm',
    name: 'IBM Quantum',
    logo: 'ibm-logo.png',
    architecture: quantumArchitectures.ibm,
    costPerHour: 125,
    queueTime: 45,
    availability: 92
  },
  {
    id: 'google',
    name: 'Google Quantum AI',
    logo: 'google-logo.png',
    architecture: quantumArchitectures.google,
    costPerHour: 180,
    queueTime: 60,
    availability: 85
  },
  {
    id: 'rigetti',
    name: 'Rigetti Computing',
    logo: 'rigetti-logo.png',
    architecture: quantumArchitectures.rigetti,
    costPerHour: 100,
    queueTime: 30,
    availability: 88
  },
  {
    id: 'ionq',
    name: 'IonQ',
    logo: 'ionq-logo.png',
    architecture: quantumArchitectures.ionq,
    costPerHour: 220,
    queueTime: 90,
    availability: 78
  }
];

// Sample quantum circuits
const sampleCircuits: QuantumCircuit[] = [
  {
    id: 'bell-pair',
    name: 'Bell Pair',
    qubits: 2,
    gates: [
      { id: 'h1', type: 'H', qubits: [0] },
      { id: 'cx1', type: 'CNOT', qubits: [0, 1] }
    ],
    depth: 2
  },
  {
    id: 'grover-2qubit',
    name: 'Grover (2-qubit)',
    qubits: 2,
    gates: [
      { id: 'h1', type: 'H', qubits: [0] },
      { id: 'h2', type: 'H', qubits: [1] },
      { id: 'x1', type: 'X', qubits: [1] },
      { id: 'h3', type: 'H', qubits: [1] },
      { id: 'cx1', type: 'CNOT', qubits: [0, 1] },
      { id: 'h4', type: 'H', qubits: [1] },
      { id: 'x2', type: 'X', qubits: [1] },
      { id: 'h5', type: 'H', qubits: [1] },
      { id: 'x3', type: 'X', qubits: [0] },
      { id: 'h6', type: 'H', qubits: [0] },
      { id: 'cx2', type: 'CNOT', qubits: [1, 0] },
      { id: 'h7', type: 'H', qubits: [0] },
      { id: 'x4', type: 'X', qubits: [0] },
      { id: 'h8', type: 'H', qubits: [0] },
      { id: 'h9', type: 'H', qubits: [1] }
    ],
    depth: 9
  },
  {
    id: 'qft-4qubit',
    name: 'QFT (4-qubit)',
    qubits: 4,
    gates: [
      // Simplified QFT gates for brevity
      { id: 'h1', type: 'H', qubits: [0] },
      { id: 'cp1', type: 'CP', qubits: [0, 1], parameters: [Math.PI/2] },
      { id: 'cp2', type: 'CP', qubits: [0, 2], parameters: [Math.PI/4] },
      { id: 'cp3', type: 'CP', qubits: [0, 3], parameters: [Math.PI/8] },
      { id: 'h2', type: 'H', qubits: [1] },
      { id: 'cp4', type: 'CP', qubits: [1, 2], parameters: [Math.PI/2] },
      { id: 'cp5', type: 'CP', qubits: [1, 3], parameters: [Math.PI/4] },
      { id: 'h3', type: 'H', qubits: [2] },
      { id: 'cp6', type: 'CP', qubits: [2, 3], parameters: [Math.PI/2] },
      { id: 'h4', type: 'H', qubits: [3] },
      // Swaps would be here in a full QFT
    ],
    depth: 10
  }
];

// Custom gate types for the circuit builder
const gateTypes = [
  { id: 'x', name: 'X', color: '#e53935', description: 'Pauli-X Gate (NOT)' },
  { id: 'y', name: 'Y', color: '#8e24aa', description: 'Pauli-Y Gate' },
  { id: 'z', name: 'Z', color: '#1e88e5', description: 'Pauli-Z Gate' },
  { id: 'h', name: 'H', color: '#43a047', description: 'Hadamard Gate' },
  { id: 'cnot', name: 'CNOT', color: '#fb8c00', description: 'Controlled NOT Gate' },
  { id: 't', name: 'T', color: '#26c6da', description: 'T Gate (π/4 phase)' },
  { id: 's', name: 'S', color: '#5e35b1', description: 'S Gate (π/2 phase)' },
  { id: 'rx', name: 'Rx', color: '#d81b60', description: 'Rotation around X-axis' },
  { id: 'ry', name: 'Ry', color: '#3949ab', description: 'Rotation around Y-axis' },
  { id: 'rz', name: 'Rz', color: '#00acc1', description: 'Rotation around Z-axis' },
  { id: 'swap', name: 'SWAP', color: '#7cb342', description: 'Swap Gate' },
  { id: 'cz', name: 'CZ', color: '#f4511e', description: 'Controlled-Z Gate' }
];

// Utility function to estimate provider-specific execution
const estimateProviderExecution = (
  circuit: QuantumCircuit,
  provider: QuantumProvider,
  enableFaultTolerance: boolean
): ProviderEstimation => {
  // Check if provider can handle the circuit
  if (provider.architecture.qubitCount < circuit.qubits) {
    return {
      providerId: provider.id,
      providerName: provider.name,
      estimatedCost: 0,
      estimatedTime: 0,
      success: false,
      errorMessage: 'Insufficient qubits',
      recommended: false
    };
  }
  
  // Check if provider supports all gate types
  const circuitGateTypes = new Set(circuit.gates.map(g => g.type));
  const unsupportedGates = Array.from(circuitGateTypes).filter(
    gate => !provider.architecture.gateSet.includes(gate)
  );
  
  if (unsupportedGates.length > 0) {
    return {
      providerId: provider.id,
      providerName: provider.name,
      estimatedCost: 0,
      estimatedTime: 0,
      success: false,
      errorMessage: `Unsupported gates: ${unsupportedGates.join(', ')}`,
      recommended: false
    };
  }
  
  // Perform comprehensive resource estimation
  const resources = estimateQuantumResources(circuit, provider.architecture, {
    faultTolerant: enableFaultTolerance,
    targetLogicalErrorRate: 1e-12
  });
  
  // Add timestamp for UI purposes
  const resourceEstimation: ResourceEstimation = {
    ...resources,
    analysisTimestamp: Date.now()
  };
  
  // Calculate provider-specific execution time (in seconds)
  const executionTimeSeconds = resources.executionTime / 1e9;
  
  // Calculate cost based on provider rates and execution time
  // Add overhead for fault tolerance if enabled
  const baseCost = provider.costPerHour * (executionTimeSeconds / 3600);
  const costFactor = enableFaultTolerance ? 
    (resources.physicalQubitCount / provider.architecture.qubitCount) : 
    (resources.circuitWidth / provider.architecture.qubitCount);
  
  const estimatedCost = baseCost * (1 + costFactor);
  
  // Total time including queue time (in seconds)
  const totalTime = executionTimeSeconds + provider.queueTime * 60;
  
  return {
    providerId: provider.id,
    providerName: provider.name,
    estimatedCost: estimatedCost,
    estimatedTime: totalTime,
    success: true,
    recommended: false,
    resourceEstimation
  };
};

// Main component
const QuantumOrchestra: React.FC = () => {
  // State for the current circuit
  const [currentCircuit, setCurrentCircuit] = useState<QuantumCircuit>(sampleCircuits[0]);
  const [customCircuit, setCustomCircuit] = useState<QuantumCircuit>({
    id: 'custom',
    name: 'Custom Circuit',
    qubits: 3,
    gates: [],
    depth: 0
  });
  
  // State for resource estimation
  const [resources, setResources] = useState<ResourceEstimation | null>(null);
  
  // State for provider estimations
  const [providerEstimations, setProviderEstimations] = useState<ProviderEstimation[]>([]);
  
  // State for UI
  const [activeTab, setActiveTab] = useState<string>('circuit');
  const [isCustomCircuit, setIsCustomCircuit] = useState<boolean>(false);
  const [selectedGateType, setSelectedGateType] = useState<string>('h');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState<boolean>(false);
  const [enableFaultTolerance, setEnableFaultTolerance] = useState<boolean>(false);
  const [targetErrorRate, setTargetErrorRate] = useState<string>("1e-12");
  const [selectedMetricsView, setSelectedMetricsView] = useState<string>("basic");
  
  // Effect to calculate resources when circuit changes
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate calculation delay
    const timer = setTimeout(() => {
      const circuit = isCustomCircuit ? customCircuit : currentCircuit;
      
      // Calculate provider-specific estimations
      const estimations = quantumProviders.map(provider => 
        estimateProviderExecution(circuit, provider, enableFaultTolerance)
      );
      
      // Find the best provider based on cost and time
      if (estimations.some(e => e.success)) {
        const successfulEstimations = estimations.filter(e => e.success);
        
        // Normalize cost and time for scoring
        const maxCost = Math.max(...successfulEstimations.map(e => e.estimatedCost));
        const maxTime = Math.max(...successfulEstimations.map(e => e.estimatedTime));
        
        // Calculate score (lower is better)
        const scores = successfulEstimations.map(e => ({
          ...e,
          score: (e.estimatedCost / maxCost) * 0.7 + (e.estimatedTime / maxTime) * 0.3
        }));
        
        // Sort by score
        scores.sort((a, b) => (a as any).score - (b as any).score);
        
        // Mark the best as recommended
        const bestProviderId = scores[0].providerId;
        
        const updatedEstimations = estimations.map(e => ({
          ...e,
          recommended: e.providerId === bestProviderId
        }));
        
        setProviderEstimations(updatedEstimations);
        
        // Set the resources from the recommended provider's estimation
        const recommendedEstimation = updatedEstimations.find(e => e.recommended);
        if (recommendedEstimation && recommendedEstimation.resourceEstimation) {
          setResources(recommendedEstimation.resourceEstimation);
        }
      } else {
        setProviderEstimations(estimations);
        setResources(null);
      }
      
      setIsLoading(false);
    }, 800);
    
    return () => clearTimeout(timer);
  }, [currentCircuit, customCircuit, isCustomCircuit, enableFaultTolerance, targetErrorRate]);
  
  // Handler for circuit selection
  const handleCircuitSelect = (circuitId: string) => {
    if (circuitId === 'custom') {
      setIsCustomCircuit(true);
    } else {
      const selectedCircuit = sampleCircuits.find(c => c.id === circuitId);
      if (selectedCircuit) {
        setCurrentCircuit(selectedCircuit);
        setIsCustomCircuit(false);
      }
    }
  };
  
  // Handler for adding a gate to the custom circuit
  const handleAddGate = () => {
    const newGate: QuantumGate = {
      id: `gate-${customCircuit.gates.length + 1}`,
      type: selectedGateType.toUpperCase(),
      qubits: selectedGateType === 'cnot' || selectedGateType === 'cz' || selectedGateType === 'swap' 
        ? [0, 1] // Two-qubit gates
        : [0]    // Single-qubit gates
    };
    
    setCustomCircuit(prev => ({
      ...prev,
      gates: [...prev.gates, newGate],
      depth: calculateCircuitDepth({
        ...prev,
        gates: [...prev.gates, newGate]
      })
    }));
  };
  
  // Handler for changing qubit count in custom circuit
  const handleQubitCountChange = (count: number) => {
    setCustomCircuit(prev => ({
      ...prev,
      qubits: count,
      // Filter out gates that reference non-existent qubits
      gates: prev.gates.filter(gate => 
        gate.qubits.every(q => q < count)
      )
    }));
  };
  
  // Handler for clearing the custom circuit
  const handleClearCircuit = () => {
    setCustomCircuit(prev => ({
      ...prev,
      gates: [],
      depth: 0
    }));
  };

  // Handler for toggling fault tolerance
  const handleToggleFaultTolerance = () => {
    setEnableFaultTolerance(!enableFaultTolerance);
  };
  
  // Helper to format time in a human-readable way
  const formatTime = (timeInSeconds: number): string => {
    if (timeInSeconds < 0.001) {
      return `${(timeInSeconds * 1e6).toFixed(2)} ns`;
    } else if (timeInSeconds < 1) {
      return `${(timeInSeconds * 1000).toFixed(2)} ms`;
    } else if (timeInSeconds < 60) {
      return `${timeInSeconds.toFixed(2)} sec`;
    } else if (timeInSeconds < 3600) {
      return `${(timeInSeconds / 60).toFixed(2)} min`;
    } else {
      return `${(timeInSeconds / 3600).toFixed(2)} hours`;
    }
  };

  // Helper to render metric cards based on selected view
  const renderMetricCards = () => {
    if (!resources) return null;

    // Basic metrics always shown
    const basicMetrics = (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Gate Count</div>
          <div className="text-2xl font-bold">{resources.totalGateCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.totalGateCount < 10 ? 'Simple circuit' : 
             resources.totalGateCount < 50 ? 'Moderate complexity' : 
             'Complex circuit'}
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Circuit Depth</div>
          <div className="text-2xl font-bold">{resources.circuitDepth}</div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.circuitDepth < 5 ? 'Shallow circuit' : 
             resources.circuitDepth < 15 ? 'Medium depth' : 
             'Deep circuit'}
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            {enableFaultTolerance ? 'Logical Qubits' : 'Required Qubits'}
          </div>
          <div className="text-2xl font-bold">{enableFaultTolerance ? resources.logicalQubitCount : resources.circuitWidth}</div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.circuitWidth < 5 ? 'Few qubits' : 
             resources.circuitWidth < 50 ? 'Moderate scale' : 
             'Large scale quantum'}
          </div>
        </div>
      </div>
    );

    // Advanced metrics shown when selected
    const advancedMetrics = selectedMetricsView === "advanced" && (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Quantum Volume</div>
          <div className="text-2xl font-bold">{resources.quantumVolume.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">
            2^{Math.log2(resources.quantumVolume).toFixed(0)} circuit capacity
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">T-Gate Count</div>
          <div className="text-2xl font-bold">{resources.tGateCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            Critical for fault-tolerance
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">SWAP Overhead</div>
          <div className="text-2xl font-bold">{resources.swapOverhead}</div>
          <div className="text-xs text-gray-500 mt-1">
            Additional gates needed for connectivity
          </div>
        </div>
      </div>
    );

    // Time and error metrics
    const timeErrorMetrics = (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Estimated Execution Time</div>
          <div className="text-2xl font-bold">
            {formatTime(resources.executionTime / 1e9)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.executionTime < 1e8 ? 'Fast execution' : 
             resources.executionTime < 1e9 ? 'Moderate duration' : 
             'Long-running computation'}
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Error Rate</div>
          <div className="text-2xl font-bold">{(resources.errorRate * 100).toFixed(2)}%</div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.errorRate < 0.01 ? 'Low error probability' : 
             resources.errorRate < 0.1 ? 'Moderate error risk' : 
             'High error probability'}
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
            {selectedMetricsView === "advanced" ? "Noise Resilience" : "Circuit Fidelity"}
          </div>
          <div className="text-2xl font-bold">
            {selectedMetricsView === "advanced" 
              ? `${(resources.noiseResilienceScore * 100).toFixed(0)}%`
              : `${(resources.fidelity * 100).toFixed(2)}%`}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {selectedMetricsView === "advanced"
              ? (resources.noiseResilienceScore > 0.7 ? 'Highly resilient' : 
                 resources.noiseResilienceScore > 0.4 ? 'Moderately resilient' : 
                 'Low resilience')
              : (resources.fidelity > 0.9 ? 'High fidelity' : 
                 resources.fidelity > 0.7 ? 'Moderate fidelity' : 
                 'Low fidelity')}
          </div>
        </div>
      </div>
    );

    // Fault tolerance metrics shown when enabled
    const faultToleranceMetrics = enableFaultTolerance && (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border-l-4 border-indigo-500">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Physical Qubits Required</div>
          <div className="text-2xl font-bold">{resources.physicalQubitCount.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">
            For error correction
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border-l-4 border-indigo-500">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Code Distance</div>
          <div className="text-2xl font-bold">{resources.distanceRequired}</div>
          <div className="text-xs text-gray-500 mt-1">
            Surface code parameter
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border-l-4 border-indigo-500">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Resource States</div>
          <div className="text-2xl font-bold">{resources.resourceStateCount}</div>
          <div className="text-xs text-gray-500 mt-1">
            Magic states for T gates
          </div>
        </div>
      </div>
    );

    // Classical resources shown in advanced view
    const classicalResources = selectedMetricsView === "advanced" && (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Classical Preprocessing</div>
          <div className="text-2xl font-bold">{resources.classicalPreprocessingComplexity}</div>
          <div className="text-xs text-gray-500 mt-1">
            Computational complexity
          </div>
        </div>
        
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Memory Requirements</div>
          <div className="text-2xl font-bold">{resources.classicalMemoryRequirements.toFixed(0)} MB</div>
          <div className="text-xs text-gray-500 mt-1">
            {resources.classicalMemoryRequirements < 100 ? 'Low memory usage' : 
             resources.classicalMemoryRequirements < 1000 ? 'Moderate memory usage' : 
             'High memory requirements'}
          </div>
        </div>
      </div>
    );

    // Coherence analysis shown in advanced view
    const coherenceAnalysis = selectedMetricsView === "advanced" && (
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
        <div className="flex items-center mb-2">
          <div className="text-sm text-gray-500 dark:text-gray-400 mr-2">Coherence Analysis</div>
          {resources.coherenceLimited && (
            <div className="flex items-center text-amber-600 dark:text-amber-400 text-xs">
              <AlertTriangle className="h-3 w-3 mr-1" />
              <span>Coherence limited</span>
            </div>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-lg font-bold">{(resources.requiredCoherenceTime).toFixed(1)} μs</div>
            <div className="text-xs text-gray-500">Required coherence time</div>
          </div>
          <div className="h-8 w-px bg-gray-300 dark:bg-gray-600 mx-4"></div>
          <div>
            <div className="text-lg font-bold">{formatTime(resources.executionTime / 1e9)}</div>
            <div className="text-xs text-gray-500">Total execution time</div>
          </div>
          <div className="h-8 w-px bg-gray-300 dark:bg-gray-600 mx-4"></div>
          <div>
            <div className="text-lg font-bold">{resources.coherenceLimited ? "Yes" : "No"}</div>
            <div className="text-xs text-gray-500">Coherence limited</div>
          </div>
        </div>
      </div>
    );

    return (
      <>
        {basicMetrics}
        {advancedMetrics}
        {timeErrorMetrics}
        {faultToleranceMetrics}
        {classicalResources}
        {coherenceAnalysis}
      </>
    );
  };
  
  return (
    <div className="flex flex-col min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-800 to-indigo-900 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Cpu className="h-8 w-8" />
              <div>
                <h1 className="text-2xl font-bold">Quantum Orchestra</h1>
                <p className="text-sm opacity-80">Quantum Resource Estimation & Management</p>
              </div>
            </div>
            
            <nav className="hidden md:flex space-x-6">
              <button 
                className={`px-3 py-2 rounded-md transition ${activeTab === 'circuit' ? 'bg-white/20' : 'hover:bg-white/10'}`}
                onClick={() => setActiveTab('circuit')}
              >
                Circuit Design
              </button>
              <button 
                className={`px-3 py-2 rounded-md transition ${activeTab === 'estimation' ? 'bg-white/20' : 'hover:bg-white/10'}`}
                onClick={() => setActiveTab('estimation')}
              >
                Resource Estimation
              </button>
              <button 
                className={`px-3 py-2 rounded-md transition ${activeTab === 'providers' ? 'bg-white/20' : 'hover:bg-white/10'}`}
                onClick={() => setActiveTab('providers')}
              >
                Providers
              </button>
              <button 
                className={`px-3 py-2 rounded-md transition ${activeTab === 'monitor' ? 'bg-white/20' : 'hover:bg-white/10'}`}
                onClick={() => setActiveTab('monitor')}
              >
                Monitor
              </button>
            </nav>
            
            <div className="flex items-center space-x-3">
              <button className="p-2 rounded-full hover:bg-white/10 transition">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <main className="flex-grow container mx-auto px-4 py-6">
        {/* Circuit Input Section */}
        <div className={`mb-8 ${activeTab !== 'circuit' && 'hidden'}`}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">Quantum Circuit Design</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Circuit
              </label>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {sampleCircuits.map(circuit => (
                  <button
                    key={circuit.id}
                    className={`p-3 rounded-md border text-left transition
                      ${!isCustomCircuit && currentCircuit.id === circuit.id 
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30' 
                        : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300'}`}
                    onClick={() => handleCircuitSelect(circuit.id)}
                  >
                    <div className="font-medium">{circuit.name}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {circuit.qubits} qubits, {circuit.gates.length} gates
                    </div>
                  </button>
                ))}
                <button
                  className={`p-3 rounded-md border text-left transition
                    ${isCustomCircuit 
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300'}`}
                  onClick={() => handleCircuitSelect('custom')}
                >
                  <div className="font-medium">Custom Circuit</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Build your own circuit
                  </div>
                </button>
              </div>
            </div>
            
            {isCustomCircuit && (
              <div className="border rounded-lg p-4 dark:border-gray-700">
                <div className="flex flex-wrap gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Number of Qubits
                    </label>
                    <div className="flex items-center space-x-2">
                      <button 
                        className="w-8 h-8 rounded border border-gray-300 dark:border-gray-600 flex items-center justify-center"
                        onClick={() => handleQubitCountChange(Math.max(1, customCircuit.qubits - 1))}
                        disabled={customCircuit.qubits <= 1}
                      >
                        -
                      </button>
                      <span className="w-8 text-center">{customCircuit.qubits}</span>
                      <button 
                        className="w-8 h-8 rounded border border-gray-300 dark:border-gray-600 flex items-center justify-center"
                        onClick={() => handleQubitCountChange(Math.min(20, customCircuit.qubits + 1))}
                        disabled={customCircuit.qubits >= 20}
                      >
                        +
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Gate Type
                    </label>
                    <select 
                      className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5"
                      value={selectedGateType}
                      onChange={(e) => setSelectedGateType(e.target.value)}
                    >
                      {gateTypes.map(gate => (
                        <option key={gate.id} value={gate.id}>{gate.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex items-end">
                    <button 
                      className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-md px-4 py-1.5 flex items-center space-x-1"
                      onClick={handleAddGate}
                    >
                      <CirclePlus className="h-4 w-4" />
                      <span>Add Gate</span>
                    </button>
                  </div>
                  
                  <div className="flex items-end ml-auto">
                    <button 
                      className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md px-4 py-1.5"
                      onClick={handleClearCircuit}
                    >
                      Clear Circuit
                    </button>
                  </div>
                </div>
                
                {/* Circuit Visualization */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 mb-4 overflow-x-auto">
                  <div className="font-mono whitespace-nowrap">
                    {customCircuit.qubits > 0 && Array.from({ length: customCircuit.qubits }).map((_, qubitIndex) => (
                      <div key={qubitIndex} className="flex items-center mb-4">
                        <div className="w-10 text-right mr-3 text-gray-500">q{qubitIndex}:</div>
                        <div className="h-px bg-gray-300 dark:bg-gray-600 flex-grow relative">
                          {customCircuit.gates
                            .filter(gate => gate.qubits.includes(qubitIndex))
                            .map((gate, gateIndex) => {
                              // This is a simplified visualization - a real app would have proper circuit rendering
                              const gateType = gateTypes.find(g => g.id === gate.type.toLowerCase());
                              const isControlQubit = gate.type === 'CNOT' && gate.qubits[0] === qubitIndex;
                              const isTargetQubit = gate.type === 'CNOT' && gate.qubits[1] === qubitIndex;
                              
                              return (
                                <div 
                                  key={`${gate.id}-${gateIndex}`} 
                                  className={`absolute top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm`}
                                  style={{ 
                                    left: `${gateIndex * 40}px`,
                                    backgroundColor: gateType?.color || '#888',
                                    border: isControlQubit ? '2px solid white' : 'none'
                                  }}
                                >
                                  {isControlQubit ? '•' : (isTargetQubit ? '⊕' : gateType?.name || gate.type)}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {customCircuit.gates.length === 0 && (
                    <div className="text-center text-gray-500 py-8">
                      Add gates to visualize your circuit
                    </div>
                  )}
                </div>
                
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Gates: {customCircuit.gates.length} | 
                  Depth: {customCircuit.depth} | 
                  Qubits: {customCircuit.qubits}
                </div>
              </div>
            )}
            
            {!isCustomCircuit && (
              <div className="border rounded-lg p-4 dark:border-gray-700">
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 mb-4 overflow-x-auto">
                  <div className="font-mono whitespace-nowrap">
                    {Array.from({ length: currentCircuit.qubits }).map((_, qubitIndex) => (
                      <div key={qubitIndex} className="flex items-center mb-4">
                        <div className="w-10 text-right mr-3 text-gray-500">q{qubitIndex}:</div>
                        <div className="h-px bg-gray-300 dark:bg-gray-600 flex-grow relative">
                          {currentCircuit.gates
                            .filter(gate => gate.qubits.includes(qubitIndex))
                            .map((gate, gateIndex) => {
                              const gateType = gateTypes.find(g => g.id === gate.type.toLowerCase());
                              const isControlQubit = gate.type === 'CNOT' && gate.qubits[0] === qubitIndex;
                              const isTargetQubit = gate.type === 'CNOT' && gate.qubits[1] === qubitIndex;
                              
                              return (
                                <div 
                                  key={`${gate.id}-${gateIndex}`} 
                                  className={`absolute top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm`}
                                  style={{ 
                                    left: `${gateIndex * 40}px`,
                                    backgroundColor: gateType?.color || '#888',
                                    border: isControlQubit ? '2px solid white' : 'none'
                                  }}
                                >
                                  {isControlQubit ? '•' : (isTargetQubit ? '⊕' : gateType?.name || gate.type)}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Gates: {currentCircuit.gates.length} | 
                  Depth: {currentCircuit.depth} | 
                  Qubits: {currentCircuit.qubits}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Resource Estimation Panel */}
        <div className={`mb-8 ${activeTab !== 'estimation' && activeTab !== 'circuit' && 'hidden'}`}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Resource Estimation</h2>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Metrics:</span>
                  <select 
                    className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-sm"
                    value={selectedMetricsView}
                    onChange={(e) => setSelectedMetricsView(e.target.value)}
                  >
                    <option value="basic">Basic</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                
                <button 
                  className="flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                  onClick={() => {
                    setIsLoading(true);
                    setTimeout(() => setIsLoading(false), 800);
                  }}
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>
            
            {/* Fault Tolerance Toggle */}
            <div className="mb-6 flex items-center justify-between bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3">
              <div className="flex items-center">
                <Shield className="h-5 w-5 text-indigo-600 dark:text-indigo-400 mr-2" />
                <div>
                  <div className="font-medium">Fault Tolerance</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Enable error correction for reliable quantum computation
                  </div>
                </div>
              </div>
              
              <button 
                className="flex items-center space-x-2"
                onClick={handleToggleFaultTolerance}
              >
                {enableFaultTolerance ? (
                  <>
                    <ToggleRight className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                    <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Enabled</span>
                  </>
                ) : (
                  <>
                    <ToggleLeft className="h-6 w-6 text-gray-400 dark:text-gray-600" />
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Disabled</span>
                  </>
                )}
              </button>
            </div>
            
            {isLoading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              </div>
            ) : resources ? (
              renderMetricCards()
            ) : (
              <div className="text-center py-8 text-gray-500">
                Select a circuit to see resource estimation
              </div>
            )}
            
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-2">
              <button
                className="flex items-center text-sm text-gray-600 dark:text-gray-400"
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              >
                <ChevronDown className={`h-4 w-4 mr-1 transition-transform ${showAdvancedOptions ? 'rotate-180' : ''}`} />
                Advanced Options
              </button>
              
              {showAdvancedOptions && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Error Correction Level
                    </label>
                    <select 
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5"
                      disabled={!enableFaultTolerance}
                    >
                      <option>None (Physical Qubits)</option>
                      <option>Surface Code (d=3)</option>
                      <option>Surface Code (d=5)</option>
                      <option>Surface Code (d=7)</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Target Logical Error Rate
                    </label>
                    <select 
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5"
                      value={targetErrorRate}
                      onChange={(e) => setTargetErrorRate(e.target.value)}
                      disabled={!enableFaultTolerance}
                    >
                      <option value="1e-6">10^-6 (Low Precision)</option>
                      <option value="1e-9">10^-9 (Medium Precision)</option>
                      <option value="1e-12">10^-12 (High Precision)</option>
                      <option value="1e-15">10^-15 (Very High Precision)</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Optimization Level
                    </label>
                    <select className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5">
                      <option>None</option>
                      <option>Basic Gate Fusion</option>
                      <option>Advanced Optimization</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Hardware Constraints
                    </label>
                    <select className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-1.5">
                      <option>Ideal (No Constraints)</option>
                      <option>Realistic Connectivity</option>
                      <option>Realistic Noise Model</option>
                      <option>Full Hardware Model</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Provider Comparison */}
        <div className={`mb-8 ${activeTab !== 'providers' && activeTab !== 'estimation' && 'hidden'}`}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-white">Quantum Provider Comparison</h2>
            
            {isLoading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              </div>
            ) : providerEstimations.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Provider</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estimated Cost</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Execution Time</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {enableFaultTolerance ? "Physical Qubits" : "Circuit Fidelity"}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Recommended</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {providerEstimations.map((estimation, index) => {
                      const provider = quantumProviders.find(p => p.id === estimation.providerId);
                      
                      return (
                        <tr key={estimation.providerId} className={index % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900/50' : ''}>
                          <td className="px-4 py-4">
                            <div className="flex items-center">
                              <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 mr-3 flex items-center justify-center text-xs">
                                {provider?.name.charAt(0)}
                              </div>
                              <div>
                                <div className="font-medium">{provider?.name}</div>
                                <div className="text-xs text-gray-500">
                                  {provider?.architecture.name}, {provider?.architecture.qubitCount} qubits
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            {estimation.success ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                                Compatible
                              </span>
                            ) : (
                              <div>
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                                  Incompatible
                                </span>
                                <div className="text-xs text-red-600 dark:text-red-400 mt-1">
                                  {estimation.errorMessage}
                                </div>
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            {estimation.success ? (
                              <div className="font-medium">${estimation.estimatedCost.toFixed(2)}</div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            {estimation.success && estimation.resourceEstimation ? (
                              <div>
                                {formatTime(estimation.resourceEstimation.executionTime / 1e9)}
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            {estimation.success && estimation.resourceEstimation ? (
                              <div>
                                {enableFaultTolerance ? 
                                  estimation.resourceEstimation.physicalQubitCount.toLocaleString() :
                                  `${(estimation.resourceEstimation.fidelity * 100).toFixed(2)}%`
                                }
                              </div>
                            ) : (
                              <span className="text-gray-400">N/A</span>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            {estimation.recommended ? (
                              <div className="flex items-center text-green-600 dark:text-green-400">
                                <Check className="h-5 w-5 mr-1" />
                                <span>Best Choice</span>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Select a circuit to see provider comparisons
              </div>
            )}
            
            {/* Provider Details */}
            {providerEstimations.some(e => e.success) && (
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium mb-4">Provider Architecture Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {quantumProviders.map(provider => (
                    <div key={provider.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-3">
                        <div className="font-medium">{provider.name}</div>
                        <div className="text-sm text-gray-500">{provider.architecture.qubitCount} qubits</div>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Connectivity:</span>
                          <span>{provider.architecture.connectivity}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">1-Qubit Gate Error:</span>
                          <span>{provider.architecture.gateErrors['single-qubit'].toExponential(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">2-Qubit Gate Error:</span>
                          <span>{provider.architecture.gateErrors['two-qubit'].toExponential(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">T1 Time:</span>
                          <span>{provider.architecture.t1Times[0]} μs</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Gate Time (2Q):</span>
                          <span>{provider.architecture.gateTimings['two-qubit']} ns</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Real-time Resource Monitor */}
        <div className={`mb-8 ${activeTab !== 'monitor' && 'hidden'}`}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Quantum Resource Monitor</h2>
              
              <button 
                className="flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh</span>
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium mb-3">Provider Availability</h3>
                
                <div className="space-y-4">
                  {quantumProviders.map(provider => (
                    <div key={provider.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                      <div className="flex justify-between items-center mb-2">
                        <div className="font-medium">{provider.name}</div>
                        <div className={`text-sm ${
                          provider.availability > 90 ? 'text-green-600 dark:text-green-400' :
                          provider.availability > 70 ? 'text-yellow-600 dark:text-yellow-400' :
                          'text-red-600 dark:text-red-400'
                        }`}>
                          {provider.availability}% Available
                        </div>
                      </div>
                      
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5">
                        <div 
                          className={`h-2.5 rounded-full ${
                            provider.availability > 90 ? 'bg-green-500' :
                            provider.availability > 70 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${provider.availability}%` }}
                        ></div>
                      </div>
                      
                      <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        Queue time: ~{provider.queueTime} minutes
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-3">Active Jobs</h3>
                
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
                  <div className="flex justify-between items-center mb-3">
                    <div>
                      <div className="font-medium">QFT Simulation</div>
                      <div className="text-sm text-gray-500">IBM Quantum</div>
                    </div>
                    <div className="text-sm px-2.5 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                      Running
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5 mb-2">
                    <div className="h-2.5 rounded-full bg-blue-500" style={{ width: '75%' }}></div>
                  </div>
                  
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    75% complete • 3 minutes remaining
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-3">
                    <div>
                      <div className="font-medium">Grover Search</div>
                      <div className="text-sm text-gray-500">Google Quantum AI</div>
                    </div>
                    <div className="text-sm px-2.5 py-1 rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                      Queued
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Position 3 in queue • ~45 minutes wait
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="text-lg font-medium mb-3">Usage Statistics</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Monthly Usage</div>
                  <div className="text-2xl font-bold">43.2 hours</div>
                  <div className="text-xs text-gray-500 mt-1">
                    72% of your monthly allocation
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Cost</div>
                  <div className="text-2xl font-bold">$1,245.00</div>
                  <div className="text-xs text-gray-500 mt-1">
                    This billing period
                  </div>
                </div>
                
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Jobs Completed</div>
                  <div className="text-2xl font-bold">37</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Last 30 days
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-4">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-4 md:mb-0">
              Quantum Orchestra v1.0.0 • Quantum Resource Estimation & Management
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                Documentation
              </button>
              <button className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                Support
              </button>
              <button className="flex items-center space-x-1 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300">
                <Info className="h-4 w-4" />
                <span>About</span>
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default QuantumOrchestra;
