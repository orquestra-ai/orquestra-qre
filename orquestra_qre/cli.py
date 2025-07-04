#!/usr/bin/env python3
"""
Command-line interface for Orquestra QRE.
Provides batch processing capabilities and automation tools.
"""

import argparse
import json
import sys
from typing import List, Dict, Any

from .quantum import QuantumCircuit, QuantumGate, CircuitGenerator, QuantumResourceEstimator

def create_circuit_from_args(args) -> QuantumCircuit:
    """Create a quantum circuit based on command line arguments."""
    generator = CircuitGenerator()
    
    if args.circuit_type == "bell":
        return generator.generate_bell_state()
    elif args.circuit_type == "grover":
        return generator.generate_grover_search(args.num_qubits or 3)
    elif args.circuit_type == "qft":
        return generator.generate_qft(args.num_qubits or 3)
    else:
        # Create a simple circuit
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        return QuantumCircuit(args.num_qubits or 2, gates, args.circuit_type or "custom")

def estimate_resources(args):
    """Estimate resources for a quantum circuit."""
    circuit = create_circuit_from_args(args)
    estimator = QuantumResourceEstimator()
    
    print(f"🔬 Analyzing circuit: {circuit.name}")
    print(f"   Qubits: {circuit.num_qubits}")
    print(f"   Gates: {len(circuit.gates)}")
    
    estimate = estimator.estimate_resources(circuit)
    
    print(f"\n📊 Resource Estimation Results:")
    print(f"   Circuit Name: {estimate.circuit_name}")
    print(f"   Qubits: {estimate.num_qubits}")
    print(f"   Circuit Depth: {estimate.depth}")
    print(f"   Total Gates: {estimate.gate_count}")
    print(f"   Estimated Runtime: {estimate.estimated_runtime_ms:.2f} ms")
    print(f"   Estimated Fidelity: {estimate.estimated_fidelity:.3f}")
    print(f"   Gate Breakdown: {estimate.gate_breakdown}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(estimate.to_dict(), f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

def list_circuits(args):
    """List available circuit types."""
    circuits = {
        "bell": "Bell state preparation circuit",
        "grover": "Grover's search algorithm",
        "qft": "Quantum Fourier Transform",
        "custom": "Custom circuit with H and CNOT gates"
    }
    
    print("🎯 Available Circuit Types:")
    for name, description in circuits.items():
        print(f"   {name}: {description}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orquestra QRE - Quantum Resource Estimation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Estimate command
    estimate_parser = subparsers.add_parser('estimate', help='Estimate circuit resources')
    estimate_parser.add_argument('--circuit-type', choices=['bell', 'grover', 'qft', 'custom'], 
                                default='bell', help='Type of circuit to analyze')
    estimate_parser.add_argument('--num-qubits', type=int, help='Number of qubits (for applicable circuits)')
    estimate_parser.add_argument('--output', '-o', help='Output file for results (JSON format)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available circuits')
    
    args = parser.parse_args()
    
    if args.command == 'estimate':
        estimate_resources(args)
    elif args.command == 'list':
        list_circuits(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()