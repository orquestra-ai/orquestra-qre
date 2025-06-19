"""
Connectivity and SWAP analysis for quantum hardware topologies.

This module provides functionality to model different quantum hardware
connectivity graphs and analyze the SWAP overhead required to execute 
logical quantum circuits on these physical hardware topologies.
"""

import networkx as nx
from typing import Dict, List, Tuple, Set, Optional
import numpy as np
import math
from dataclasses import dataclass

@dataclass
class ConnectivityGraph:
    """Model of a quantum hardware connectivity graph."""
    name: str
    edges: List[Tuple[int, int]]
    n_qubits: int
    description: str
    
    def to_dict(self):
        return {
            'name': self.name,
            'n_qubits': self.n_qubits,
            'edges': self.edges,
            'description': self.description
        }
    
    def to_networkx(self):
        """Convert to NetworkX graph for analysis."""
        G = nx.Graph()
        G.add_nodes_from(range(self.n_qubits))
        G.add_edges_from(self.edges)
        return G


# Common hardware connectivity models
def create_line_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create a linear chain connectivity graph."""
    edges = [(i, i+1) for i in range(n_qubits-1)]
    return ConnectivityGraph(
        name="Linear Chain",
        edges=edges,
        n_qubits=n_qubits,
        description="Linear nearest-neighbor connectivity"
    )

def create_ring_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create a ring connectivity graph."""
    edges = [(i, i+1) for i in range(n_qubits-1)]
    edges.append((n_qubits-1, 0))  # Close the ring
    return ConnectivityGraph(
        name="Ring",
        edges=edges,
        n_qubits=n_qubits,
        description="Ring topology with nearest-neighbor connectivity"
    )

def create_heavy_hex_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create an IBM Heavy Hex connectivity graph.
    
    This is a simplified model - a full implementation would require
    more complex layout matching to IBM's actual chip topologies.
    """
    # Start with a grid and modify for heavy hex pattern
    if n_qubits < 9:
        # Fall back to a simple grid for small n_qubits
        return create_grid_connectivity(n_qubits)
    
    width = int(math.sqrt(n_qubits))
    edges = []
    
    # Create a base grid
    for row in range(width):
        for col in range(width):
            node_id = row * width + col
            if node_id >= n_qubits:
                break
                
            # Connect to right neighbor
            if col + 1 < width and node_id + 1 < n_qubits:
                edges.append((node_id, node_id + 1))
            
            # Connect to below neighbor
            if row + 1 < width and node_id + width < n_qubits:
                edges.append((node_id, node_id + width))
                
            # Add extra connections for heavy hex pattern
            if row % 2 == 0 and col % 2 == 0:
                if row + 1 < width and col + 1 < width and node_id + width + 1 < n_qubits:
                    edges.append((node_id, node_id + width + 1))
    
    return ConnectivityGraph(
        name="Heavy Hex",
        edges=edges,
        n_qubits=n_qubits,
        description="IBM Heavy Hex inspired topology with increased connectivity"
    )

def create_grid_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create a 2D grid connectivity graph."""
    width = int(math.sqrt(n_qubits))
    edges = []
    
    for row in range(width):
        for col in range(width):
            node_id = row * width + col
            if node_id >= n_qubits:
                break
                
            # Connect to right neighbor
            if col + 1 < width and node_id + 1 < n_qubits:
                edges.append((node_id, node_id + 1))
            
            # Connect to below neighbor
            if row + 1 < width and node_id + width < n_qubits:
                edges.append((node_id, node_id + width))
    
    return ConnectivityGraph(
        name="2D Grid",
        edges=edges,
        n_qubits=n_qubits,
        description="2D Grid connectivity"
    )

def create_full_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create a fully connected graph where all qubits are connected."""
    edges = []
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            edges.append((i, j))
    
    return ConnectivityGraph(
        name="All-to-All",
        edges=edges,
        n_qubits=n_qubits,
        description="Full connectivity (all qubits connected)"
    )

def create_sycamore_connectivity(n_qubits: int) -> ConnectivityGraph:
    """Create a Google Sycamore-inspired connectivity graph."""
    if n_qubits <= 4:
        return create_full_connectivity(n_qubits)
        
    # Use maximum of 72 qubits (like Google Sycamore)
    n_qubits = min(n_qubits, 72)
    
    # Create a base grid with additional diagonal connections
    width = int(math.sqrt(n_qubits))
    edges = []
    
    for row in range(width):
        for col in range(width):
            node_id = row * width + col
            if node_id >= n_qubits:
                break
                
            # Connect to right neighbor
            if col + 1 < width and node_id + 1 < n_qubits:
                edges.append((node_id, node_id + 1))
            
            # Connect to below neighbor
            if row + 1 < width and node_id + width < n_qubits:
                edges.append((node_id, node_id + width))
            
            # Add diagonal connections in alternating pattern
            if (row + col) % 2 == 0:
                if row + 1 < width and col + 1 < width and node_id + width + 1 < n_qubits:
                    edges.append((node_id, node_id + width + 1))
    
    return ConnectivityGraph(
        name="Sycamore-inspired",
        edges=edges,
        n_qubits=n_qubits,
        description="Google Sycamore inspired connectivity pattern"
    )

# Dictionary of connectivity graph generators by provider name
CONNECTIVITY_MODELS = {
    "IBM": create_heavy_hex_connectivity,
    "Google": create_sycamore_connectivity,
    "IonQ": create_full_connectivity,
    "Rigetti": create_grid_connectivity,
    "Custom": create_full_connectivity,  # Default for custom
    "Linear": create_line_connectivity,
    "Ring": create_ring_connectivity,
    "Grid": create_grid_connectivity
}

class SWAPEstimator:
    """
    Estimates the number of additional SWAP gates required to execute
    a logical circuit on a physical hardware with limited connectivity.
    """
    
    @staticmethod
    def count_non_local_cnots(circuit, connectivity_graph: ConnectivityGraph) -> int:
        """
        Count the number of non-local CNOT gates in a circuit.
        A non-local CNOT is one that operates on qubits not directly connected in the hardware.
        """
        non_local_count = 0
        graph = connectivity_graph.to_networkx()
        edges = set(connectivity_graph.edges).union(set((b, a) for a, b in connectivity_graph.edges))
        
        for gate in circuit.gates:
            if gate.name == "CNOT" and len(gate.qubits) == 2:
                q1, q2 = gate.qubits
                # Check if this edge exists in the connectivity graph
                if (q1, q2) not in edges and (q2, q1) not in edges:
                    non_local_count += 1
        
        return non_local_count
    
    @staticmethod
    def estimate_swap_overhead(circuit, connectivity_graph: ConnectivityGraph) -> Dict:
        """
        Estimate the SWAP overhead for executing a circuit on a specific hardware topology.
        
        Returns a dictionary with:
        - non_local_cnots: Number of CNOTs that need routing
        - approx_swap_count: Estimated number of SWAP gates needed
        - swap_depth_overhead: Estimated increase in circuit depth
        - routed_gate_count: Total gates after routing
        """
        # First, check if we have enough qubits in the connectivity graph
        if circuit.num_qubits > connectivity_graph.n_qubits:
            return {
                "error": f"Circuit has {circuit.num_qubits} qubits but connectivity graph only has {connectivity_graph.n_qubits}"
            }
        
        # Count non-local CNOT gates
        non_local_cnots = SWAPEstimator.count_non_local_cnots(circuit, connectivity_graph)
        
        # If all CNOTs are local, no SWAP overhead
        if non_local_cnots == 0:
            return {
                "non_local_cnots": 0,
                "approx_swap_count": 0,
                "swap_depth_overhead": 0,
                "original_gate_count": len(circuit.gates),
                "routed_gate_count": len(circuit.gates),
                "routing_factor": 1.0
            }
        
        # Compute shortest paths between all qubit pairs
        graph = connectivity_graph.to_networkx()
        shortest_paths = dict(nx.all_pairs_shortest_path_length(graph))
        
        # Calculate average SWAP gates needed per non-local CNOT
        # For each non-local CNOT, we typically need path_length-1 SWAPs
        total_distance = 0
        total_non_local_pairs = 0
        
        for gate in circuit.gates:
            if gate.name == "CNOT" and len(gate.qubits) == 2:
                q1, q2 = gate.qubits
                # If qubits are directly connected, skip
                edge_exists = any((q1, q2) in edges or (q2, q1) in edges 
                                 for edges in [connectivity_graph.edges])
                if not edge_exists:
                    # Get shortest path length between these qubits
                    if q1 in shortest_paths and q2 in shortest_paths[q1]:
                        path_length = shortest_paths[q1][q2]
                        total_distance += path_length
                        total_non_local_pairs += 1
        
        if total_non_local_pairs == 0:
            avg_swaps_per_non_local = 0
        else:
            # Each non-local CNOT requires (path_length-1) SWAPs on average
            avg_swaps_per_non_local = (total_distance / total_non_local_pairs) - 1
        
        # Estimate total SWAP count
        approx_swap_count = math.ceil(non_local_cnots * avg_swaps_per_non_local)
        
        # Each SWAP adds 3 CNOTs to the circuit
        additional_cnots = approx_swap_count * 3
        
        # Original gate count
        original_gate_count = len(circuit.gates)
        
        # Estimated gate count after routing
        routed_gate_count = original_gate_count + additional_cnots
        
        # Routing factor (ratio of routed to original gate count)
        routing_factor = routed_gate_count / original_gate_count if original_gate_count > 0 else 1.0
        
        # Depth overhead (simplified model - assumes depth increases with SWAP count)
        # In practice, some SWAPs can be parallelized, so this is an upper bound
        swap_depth_overhead = approx_swap_count
        
        return {
            "non_local_cnots": non_local_cnots,
            "approx_swap_count": approx_swap_count,
            "swap_depth_overhead": swap_depth_overhead,
            "additional_cnots_from_swaps": additional_cnots,
            "original_gate_count": original_gate_count,
            "routed_gate_count": routed_gate_count,
            "routing_factor": routing_factor
        }
