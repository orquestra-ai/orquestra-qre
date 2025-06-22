"""
Unit tests for the connectivity module.
"""

import pytest
import math
import networkx as nx
from unittest.mock import MagicMock

from orquestra_qre.connectivity import (
    ConnectivityGraph,
    SWAPEstimator,
    CONNECTIVITY_MODELS,
    create_line_connectivity,
    create_ring_connectivity,
    create_heavy_hex_connectivity,
    create_grid_connectivity,
    create_full_connectivity,
    create_sycamore_connectivity
)
from orquestra_qre.quantum import QuantumCircuit, QuantumGate

class TestConnectivityGraph:
    """Test the ConnectivityGraph class."""
    
    def test_initialization(self):
        """Test initialization of connectivity graph."""
        # Create a simple linear connectivity graph
        graph = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        assert graph.name == "Linear"
        assert graph.n_qubits == 4
        assert len(graph.edges) == 3
        assert graph.description == "Linear connectivity"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        # Create a simple graph
        graph = ConnectivityGraph(
            name="Star",
            edges=[(0, 1), (0, 2), (0, 3)],
            n_qubits=4,
            description="Star topology"
        )
        
        # Convert to dict
        graph_dict = graph.to_dict()
        
        # Check dict fields
        assert graph_dict["name"] == "Star"
        assert graph_dict["n_qubits"] == 4
        assert len(graph_dict["edges"]) == 3
        assert graph_dict["description"] == "Star topology"
    
    def test_to_networkx(self):
        """Test conversion to NetworkX graph."""
        # Create a simple graph
        graph = ConnectivityGraph(
            name="Ring",
            edges=[(0, 1), (1, 2), (2, 3), (3, 0)],
            n_qubits=4,
            description="Ring topology"
        )
        
        # Convert to NetworkX graph
        nx_graph = graph.to_networkx()
        
        # Check graph properties
        assert nx_graph.number_of_nodes() == 4
        assert nx_graph.number_of_edges() == 4
        
        # Check that all nodes exist
        for i in range(4):
            assert i in nx_graph.nodes
        
        # Check that all edges exist
        for edge in graph.edges:
            assert nx_graph.has_edge(edge[0], edge[1])


class TestConnectivityModels:
    """Test the predefined connectivity models."""
    
    def test_model_existence(self):
        """Test that basic connectivity models exist."""
        # Check that common connectivity models are defined
        assert "IBM" in CONNECTIVITY_MODELS
        assert "Google" in CONNECTIVITY_MODELS
        assert "IonQ" in CONNECTIVITY_MODELS
        assert "Rigetti" in CONNECTIVITY_MODELS
        assert "Linear" in CONNECTIVITY_MODELS
        assert "Ring" in CONNECTIVITY_MODELS
        assert "Grid" in CONNECTIVITY_MODELS
    
    def test_create_line_connectivity(self):
        """Test creation of line connectivity."""
        n_qubits = 5
        graph = create_line_connectivity(n_qubits)
        
        assert graph.name == "Linear Chain"
        assert graph.n_qubits == n_qubits
        assert len(graph.edges) == n_qubits - 1
        
        # Check that edges form a line
        for i in range(n_qubits - 1):
            assert (i, i+1) in graph.edges
    
    def test_create_ring_connectivity(self):
        """Test creation of ring connectivity."""
        n_qubits = 5
        graph = create_ring_connectivity(n_qubits)
        
        assert graph.name == "Ring"
        assert graph.n_qubits == n_qubits
        assert len(graph.edges) == n_qubits  # n edges in a ring
        
        # Check that edges form a ring
        for i in range(n_qubits - 1):
            assert (i, i+1) in graph.edges
        assert (n_qubits-1, 0) in graph.edges  # Closing the ring
    
    def test_create_grid_connectivity(self):
        """Test creation of grid connectivity."""
        n_qubits = 9  # 3x3 grid
        graph = create_grid_connectivity(n_qubits)
        
        assert graph.name == "2D Grid"
        assert graph.n_qubits == n_qubits
        
        width = int(math.sqrt(n_qubits))
        expected_edges = 2 * width * (width - 1) // 2 + width - 1
        assert len(graph.edges) >= width * 2 - 2  # Minimum edges in a grid
        
        # Check a few key edges
        assert (0, 1) in graph.edges  # Horizontal edge in top row
        assert (0, 3) in graph.edges  # Vertical edge from top-left
        assert (4, 5) in graph.edges  # Horizontal edge in middle row
    
    def test_create_heavy_hex_connectivity(self):
        """Test creation of heavy hex connectivity."""
        # Test with small n_qubits (should fall back to grid)
        n_qubits_small = 4
        graph_small = create_heavy_hex_connectivity(n_qubits_small)
        assert graph_small.name == "2D Grid"  # Falls back to grid
        
        # Test with larger n_qubits
        n_qubits = 16  # 4x4 grid
        graph = create_heavy_hex_connectivity(n_qubits)
        
        assert graph.name == "Heavy Hex"
        assert graph.n_qubits == n_qubits
        assert len(graph.edges) > 0
        
        # Check that there are some diagonal edges in the heavy hex pattern
        has_diagonal = False
        for i, j in graph.edges:
            if abs(i - j) > 1 and abs(i - j) != int(math.sqrt(n_qubits)):
                has_diagonal = True
                break
        
        assert has_diagonal
    
    def test_create_full_connectivity(self):
        """Test creation of fully connected graph."""
        n_qubits = 5
        graph = create_full_connectivity(n_qubits)
        
        assert graph.name == "All-to-All"
        assert graph.n_qubits == n_qubits
        assert len(graph.edges) == (n_qubits * (n_qubits - 1)) // 2
        
        # Check that all possible pairs are connected
        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                assert (i, j) in graph.edges
    
    def test_create_sycamore_connectivity(self):
        """Test creation of Sycamore-inspired connectivity."""
        # Test with small n_qubits (should use full connectivity)
        n_qubits_small = 4
        graph_small = create_sycamore_connectivity(n_qubits_small)
        assert graph_small.name == "All-to-All"
        
        # Test with larger n_qubits
        n_qubits = 16  # 4x4 grid
        graph = create_sycamore_connectivity(n_qubits)
        
        assert graph.name == "Sycamore-inspired"
        assert graph.n_qubits == n_qubits
        assert len(graph.edges) > 0
        
        # Check that there are some diagonal edges in the Sycamore pattern
        has_diagonal = False
        for i, j in graph.edges:
            if abs(i - j) > 1 and abs(i - j) != int(math.sqrt(n_qubits)):
                has_diagonal = True
                break
        
        assert has_diagonal
        
        # Test that it caps at 72 qubits
        n_qubits_large = 100
        graph_large = create_sycamore_connectivity(n_qubits_large)
        assert graph_large.n_qubits == 72


class TestSWAPEstimator:
    """Test the SWAPEstimator class."""
    
    def test_count_non_local_cnots(self):
        """Test counting non-local CNOT gates."""
        # Create a test circuit with some CNOT gates
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1]),  # Local if 0-1 connected
            QuantumGate("CNOT", [0, 2]),  # Non-local if 0-2 not connected
            QuantumGate("CNOT", [1, 3]),  # Non-local if 1-3 not connected
            QuantumGate("H", [2]),
            QuantumGate("CNOT", [2, 3])   # Local if 2-3 connected
        ]
        circuit = QuantumCircuit(4, gates, "Test Circuit")
        
        # Create a linear connectivity graph (0-1-2-3)
        linear_connectivity = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        # Count non-local CNOTs
        non_local_count = SWAPEstimator.count_non_local_cnots(circuit, linear_connectivity)
        
        # In linear connectivity, CNOT[0,2] and CNOT[1,3] are non-local
        assert non_local_count == 2
        
        # Create a fully connected graph
        full_connectivity = ConnectivityGraph(
            name="Full",
            edges=[(i, j) for i in range(4) for j in range(i+1, 4)],
            n_qubits=4,
            description="Full connectivity"
        )
        
        # Count non-local CNOTs in fully connected graph
        non_local_count = SWAPEstimator.count_non_local_cnots(circuit, full_connectivity)
        
        # In fully connected graph, all CNOTs are local
        assert non_local_count == 0
    
    def test_estimate_swap_overhead_all_local(self):
        """Test SWAP overhead estimation when all gates are local."""
        # Create a test circuit with only local CNOT gates for a linear graph
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1]),  # Local
            QuantumGate("H", [1]),
            QuantumGate("CNOT", [1, 2]),  # Local
            QuantumGate("H", [2]),
            QuantumGate("CNOT", [2, 3])   # Local
        ]
        circuit = QuantumCircuit(4, gates, "Test Circuit")
        
        # Create a linear connectivity graph (0-1-2-3)
        linear_connectivity = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        # Estimate SWAP overhead
        result = SWAPEstimator.estimate_swap_overhead(circuit, linear_connectivity)
        
        # No SWAP overhead expected
        assert result["non_local_cnots"] == 0
        assert result["approx_swap_count"] == 0
        assert result["swap_depth_overhead"] == 0
        assert result["original_gate_count"] == 6
        assert result["routed_gate_count"] == 6
        assert result["routing_factor"] == 1.0
    
    def test_estimate_swap_overhead_non_local(self):
        """Test SWAP overhead estimation when some gates are non-local."""
        # Create a test circuit with non-local CNOT gates for a linear graph
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 2]),  # Non-local
            QuantumGate("H", [1]),
            QuantumGate("CNOT", [0, 3]),  # Non-local
            QuantumGate("H", [2]),
            QuantumGate("CNOT", [1, 3])   # Non-local
        ]
        circuit = QuantumCircuit(4, gates, "Test Circuit")
        
        # Create a linear connectivity graph (0-1-2-3)
        linear_connectivity = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        # Estimate SWAP overhead
        result = SWAPEstimator.estimate_swap_overhead(circuit, linear_connectivity)
        
        # Expect SWAP overhead
        assert result["non_local_cnots"] == 3
        assert result["approx_swap_count"] > 0
        assert result["swap_depth_overhead"] > 0
        assert result["original_gate_count"] == 6
        assert result["routed_gate_count"] > 6
        assert result["routing_factor"] > 1.0
        assert result["additional_cnots_from_swaps"] > 0
    
    def test_estimate_swap_overhead_circuit_too_large(self):
        """Test error handling when circuit has more qubits than connectivity graph."""
        # Create a 5-qubit circuit
        gates = [QuantumGate("H", [0]), QuantumGate("CNOT", [0, 1])]
        circuit = QuantumCircuit(5, gates, "Test Circuit")
        
        # Create a 4-qubit connectivity graph
        connectivity = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        # Estimate SWAP overhead
        result = SWAPEstimator.estimate_swap_overhead(circuit, connectivity)
        
        # Should return an error message
        assert "error" in result
        assert "Circuit has 5 qubits but connectivity graph only has 4" in result["error"]
    
    def test_estimate_swap_overhead_no_two_qubit_gates(self):
        """Test SWAP overhead estimation when there are no two-qubit gates."""
        # Create a test circuit with only single-qubit gates
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("X", [1]),
            QuantumGate("Y", [2]),
            QuantumGate("Z", [3])
        ]
        circuit = QuantumCircuit(4, gates, "Test Circuit")
        
        # Create a linear connectivity graph
        linear_connectivity = ConnectivityGraph(
            name="Linear",
            edges=[(0, 1), (1, 2), (2, 3)],
            n_qubits=4,
            description="Linear connectivity"
        )
        
        # Estimate SWAP overhead
        result = SWAPEstimator.estimate_swap_overhead(circuit, linear_connectivity)
        
        # No SWAP overhead expected
        assert result["non_local_cnots"] == 0
        assert result["approx_swap_count"] == 0
        assert result["swap_depth_overhead"] == 0
        assert result["original_gate_count"] == 4
        assert result["routed_gate_count"] == 4
        assert result["routing_factor"] == 1.0
