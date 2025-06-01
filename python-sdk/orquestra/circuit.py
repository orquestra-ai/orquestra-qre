"""
Orquestra SDK: Quantum Circuit Definitions
------------------------------------------

This module defines the core classes for representing quantum gates and quantum circuits
within the Orquestra ecosystem. It uses Pydantic for data validation and type enforcement.
"""
from typing import List, Optional, Dict, Any, Union, TypeVar, Type
from uuid import uuid4

from pydantic import BaseModel, Field, validator, root_validator

# Type variable for QuantumCircuit to use in classmethods like from_qasm
QC = TypeVar('QC', bound='QuantumCircuit')

class QuantumGate(BaseModel):
    """
    Represents a single quantum gate operation in a quantum circuit.

    Attributes:
        id (str): A unique identifier for this gate instance within a circuit.
                  Defaults to a new UUID4 string.
        type (str): The type of the quantum gate (e.g., "H", "X", "CNOT", "RX").
                    Gate types are typically case-sensitive.
        qubits (List[int]): A list of zero-indexed qubit integers that this gate acts upon.
                            For a single-qubit gate, this list contains one element.
                            For a two-qubit gate (e.g., CNOT), it contains two elements
                            (e.g., [control_qubit, target_qubit]).
        parameters (Optional[List[float]]): Optional list of numerical parameters for the gate,
                                            such as rotation angles (e.g., for RX, U3 gates).
        duration (Optional[float]): Optional specific duration for this gate instance in nanoseconds.
                                    If provided, it may override default durations from a
                                    hardware architecture model.
        fidelity (Optional[float]): Optional specific fidelity (0.0 to 1.0) for this gate instance.
                                   If provided, it may override default fidelities from a
                                   hardware architecture model.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    qubits: List[int]
    parameters: Optional[List[float]] = None
    duration: Optional[float] = Field(default=None, gt=0)
    fidelity: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @validator('qubits')
    def check_qubits_non_empty_and_non_negative(cls, v: List[int]) -> List[int]:
        """Validates that the qubits list is not empty and all indices are non-negative."""
        if not v:
            raise ValueError("Gate must act on at least one qubit.")
        if not all(idx >= 0 for idx in v):
            raise ValueError("Qubit indices must be non-negative integers.")
        if len(set(v)) != len(v):
            raise ValueError("Qubit indices for a single gate must be unique.")
        return v

    @validator('type')
    def gate_type_uppercase(cls, v: str) -> str:
        """Converts gate type to uppercase for consistency."""
        return v.upper()

    def __str__(self) -> str:
        param_str = f"({', '.join(map(str, self.parameters))})" if self.parameters else ""
        qubit_str = ', '.join(map(str, self.qubits))
        return f"{self.type}{param_str} q[{qubit_str}]"

    def __repr__(self) -> str:
        return (f"QuantumGate(id='{self.id}', type='{self.type}', qubits={self.qubits}, "
                f"parameters={self.parameters}, duration={self.duration}, fidelity={self.fidelity})")

    class Config:
        validate_assignment = True # Re-validate on attribute assignment
        frozen = False # Allow modification after creation, e.g. by circuit manipulation methods

class QuantumCircuit(BaseModel):
    """
    Represents a quantum circuit, composed of a set of qubits and a sequence of quantum gates.

    Attributes:
        id (str): A unique identifier for this circuit. Defaults to a new UUID4 string.
        name (str): A human-readable name for the circuit.
        qubits (int): The total number of qubits defined for this circuit.
                      Qubit indices in gates range from 0 to qubits-1.
        gates (List[QuantumGate]): An ordered list of QuantumGate objects representing the
                                   operations in the circuit.
        metadata (Optional[Dict[str, Any]]): Optional dictionary for storing additional
                                             information about the circuit (e.g., description,
                                             source, creation date).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    qubits: int = Field(gt=0) # Must have at least 1 qubit
    gates: List[QuantumGate] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    @validator('gates')
    def check_gate_qubits_are_within_circuit_bounds(cls, v: List[QuantumGate], values: Dict[str, Any]) -> List[QuantumGate]:
        """Validates that all qubits acted upon by gates are within the circuit's defined qubit count."""
        num_qubits = values.get('qubits')
        if num_qubits is None:
            # This can happen if 'qubits' itself fails validation, Pydantic handles that.
            return v
        for gate in v:
            for qubit_idx in gate.qubits:
                if not (0 <= qubit_idx < num_qubits):
                    raise ValueError(
                        f"Gate '{gate.id}' (type {gate.type}) acts on qubit {qubit_idx}, "
                        f"which is out of bounds for a circuit with {num_qubits} qubits (0 to {num_qubits-1})."
                    )
        return v

    @root_validator(skip_on_failure=True) # skip_on_failure ensures previous validators passed
    def check_gate_ids_are_unique(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that all gate IDs within the circuit are unique."""
        gates = values.get('gates', [])
        gate_ids = [gate.id for gate in gates]
        if len(gate_ids) != len(set(gate_ids)):
            # Find duplicate IDs for a more informative error message
            seen_ids = set()
            duplicates = set()
            for gid in gate_ids:
                if gid in seen_ids:
                    duplicates.add(gid)
                seen_ids.add(gid)
            raise ValueError(f"Duplicate gate IDs found in circuit: {list(duplicates)}")
        return values

    def add_gate(self, gate: QuantumGate, index: Optional[int] = None) -> None:
        """
        Adds a quantum gate to the circuit.

        Args:
            gate (QuantumGate): The gate to add.
            index (Optional[int]): The position at which to insert the gate.
                                   If None, appends to the end.

        Raises:
            ValueError: If the gate's qubit indices are out of bounds or if gate ID is not unique.
        """
        # Validate gate qubits against circuit's qubit count
        for qubit_idx in gate.qubits:
            if not (0 <= qubit_idx < self.qubits):
                raise ValueError(
                    f"Gate '{gate.id}' (type {gate.type}) acts on qubit {qubit_idx}, "
                    f"which is out of bounds for this circuit with {self.qubits} qubits."
                )
        
        # Check for ID uniqueness before adding
        if any(g.id == gate.id for g in self.gates):
            raise ValueError(f"Gate with ID '{gate.id}' already exists in the circuit. Gate IDs must be unique.")

        if index is None:
            self.gates.append(gate)
        else:
            self.gates.insert(index, gate)

    def add_gates(self, gates: List[QuantumGate], index: Optional[int] = None) -> None:
        """
        Adds a list of quantum gates to the circuit.

        Args:
            gates (List[QuantumGate]): The list of gates to add.
            index (Optional[int]): The starting position at which to insert the gates.
                                   If None, appends to the end.
        """
        # Validate all gates before adding any to ensure atomicity of the check
        current_gate_ids = {g.id for g in self.gates}
        new_gate_ids = {g.id for g in gates}

        # Check for duplicates within the new gates list
        if len(new_gate_ids) != len(gates):
            seen = set()
            dupes_in_new = {g.id for g in gates if g.id in seen or seen.add(g.id)} # type: ignore
            raise ValueError(f"Duplicate gate IDs found within the list of gates to be added: {list(dupes_in_new - {None})}")

        # Check for conflicts with existing gate IDs
        conflicting_ids = current_gate_ids.intersection(new_gate_ids)
        if conflicting_ids:
            raise ValueError(f"Cannot add gates. The following gate IDs already exist in the circuit: {list(conflicting_ids)}")

        for gate in gates:
            for qubit_idx in gate.qubits:
                if not (0 <= qubit_idx < self.qubits):
                    raise ValueError(
                        f"Gate '{gate.id}' (type {gate.type}) acts on qubit {qubit_idx}, "
                        f"which is out of bounds for this circuit with {self.qubits} qubits."
                    )
        
        if index is None:
            self.gates.extend(gates)
        else:
            self.gates[index:index] = gates # type: ignore

    def depth(self) -> int:
        """
        Calculates and returns the logical depth of the circuit.
        The depth is the minimum number of time steps (layers) required to execute
        the circuit, assuming gates on disjoint qubits can run in parallel.
        """
        if not self.gates:
            return 0

        qubit_finish_layer = [0] * self.qubits
        circuit_max_depth = 0

        for gate in self.gates:
            gate_start_layer = 0
            for qubit_idx in gate.qubits:
                gate_start_layer = max(gate_start_layer, qubit_finish_layer[qubit_idx])
            
            # Assuming each gate takes one logical time step for depth calculation
            gate_finish_layer = gate_start_layer + 1
            
            for qubit_idx in gate.qubits:
                qubit_finish_layer[qubit_idx] = gate_finish_layer
            
            circuit_max_depth = max(circuit_max_depth, gate_finish_layer)
            
        return circuit_max_depth

    def gate_counts(self) -> Dict[str, int]:
        """
        Counts the occurrences of each gate type in the circuit.

        Returns:
            Dict[str, int]: A dictionary where keys are gate types (str)
                            and values are their counts (int).
        """
        counts: Dict[str, int] = {}
        for gate in self.gates:
            counts[gate.type] = counts.get(gate.type, 0) + 1
        return counts

    def __len__(self) -> int:
        """Returns the total number of gates in the circuit."""
        return len(self.gates)

    def __str__(self) -> str:
        gate_summary = ", ".join(str(g) for g in self.gates[:5])
        if len(self.gates) > 5:
            gate_summary += f", ... ({len(self.gates) - 5} more)"
        return (f"QuantumCircuit(name='{self.name}', qubits={self.qubits}, "
                f"num_gates={len(self.gates)}, gates=[{gate_summary}])")

    def __repr__(self) -> str:
        return (f"QuantumCircuit(id='{self.id}', name='{self.name}', qubits={self.qubits}, "
                f"gates={self.gates!r}, metadata={self.metadata!r})")

    def to_qasm(self, version: str = "2.0") -> str:
        """
        Exports the quantum circuit to QASM 2.0 format.

        Args:
            version (str): The QASM version to target. Currently, only "2.0" is supported.

        Returns:
            str: A string representing the circuit in QASM 2.0 format.

        Raises:
            NotImplementedError: If a QASM version other than "2.0" is requested.
            ValueError: If a gate type is not supported by basic QASM 2.0.
        """
        if version != "2.0":
            raise NotImplementedError(f"QASM version {version} not supported. Only QASM 2.0 is currently available.")

        qasm_lines = [
            "OPENQASM 2.0;",
            'include "qelib1.inc";',
            f"qreg q[{self.qubits}];"
        ]
        # Could add creg if measurements were part of the model

        for gate in self.gates:
            gate_type_lower = gate.type.lower()
            qubit_args = ", ".join(f"q[{qb}]" for qb in gate.qubits)
            
            if gate_type_lower in ["x", "y", "z", "h", "s", "sdg", "t", "tdg"]:
                if len(gate.qubits) != 1:
                    raise ValueError(f"Gate {gate.type} expects 1 qubit, got {len(gate.qubits)} for gate ID {gate.id}")
                qasm_lines.append(f"{gate_type_lower} {qubit_args};")
            elif gate_type_lower in ["cx", "cnot"]: # CNOT
                if len(gate.qubits) != 2:
                    raise ValueError(f"Gate CNOT expects 2 qubits, got {len(gate.qubits)} for gate ID {gate.id}")
                qasm_lines.append(f"cx {qubit_args};")
            elif gate_type_lower == "cz":
                if len(gate.qubits) != 2:
                    raise ValueError(f"Gate CZ expects 2 qubits, got {len(gate.qubits)} for gate ID {gate.id}")
                qasm_lines.append(f"cz {qubit_args};")
            elif gate_type_lower == "swap":
                if len(gate.qubits) != 2:
                    raise ValueError(f"Gate SWAP expects 2 qubits, got {len(gate.qubits)} for gate ID {gate.id}")
                qasm_lines.append(f"swap {qubit_args};")
            elif gate_type_lower in ["rx", "ry", "rz"]:
                if len(gate.qubits) != 1:
                    raise ValueError(f"Gate {gate.type} expects 1 qubit, got {len(gate.qubits)} for gate ID {gate.id}")
                if not gate.parameters or len(gate.parameters) != 1:
                    raise ValueError(f"Gate {gate.type} expects 1 parameter, got {gate.parameters} for gate ID {gate.id}")
                param_str = f"({gate.parameters[0]})"
                qasm_lines.append(f"{gate_type_lower}{param_str} {qubit_args};")
            elif gate_type_lower == "u3": # General U3 gate
                if len(gate.qubits) != 1:
                    raise ValueError(f"Gate U3 expects 1 qubit, got {len(gate.qubits)} for gate ID {gate.id}")
                if not gate.parameters or len(gate.parameters) != 3:
                    raise ValueError(f"Gate U3 expects 3 parameters (theta, phi, lambda), got {gate.parameters} for gate ID {gate.id}")
                param_str = f"({gate.parameters[0]},{gate.parameters[1]},{gate.parameters[2]})"
                qasm_lines.append(f"u3{param_str} {qubit_args};")
            # Add more gate translations as needed (e.g., U1, U2, controlled rotations, etc.)
            else:
                # For unsupported gates, could add a comment or raise an error
                # qasm_lines.append(f"// Unsupported gate: {gate.type} on {qubit_args}")
                raise ValueError(f"QASM export not supported for gate type '{gate.type}' (ID: {gate.id}).")
        
        return "\n".join(qasm_lines)

    @classmethod
    def from_qasm(cls: Type[QC], qasm_string: str, name: Optional[str] = None, circuit_id: Optional[str] = None) -> QC:
        """
        Creates a QuantumCircuit object from a QASM 2.0 string.
        Note: This is a basic parser and may not support all QASM features.

        Args:
            qasm_string (str): The QASM 2.0 string representing the circuit.
            name (Optional[str]): Name for the created circuit. Defaults to "Circuit from QASM".
            circuit_id (Optional[str]): ID for the created circuit. Defaults to a new UUID.

        Returns:
            QuantumCircuit: A new QuantumCircuit object.

        Raises:
            ValueError: If parsing fails or unsupported QASM features are encountered.
        """
        lines = [line.strip() for line in qasm_string.splitlines() if line.strip() and not line.strip().startswith("//")]

        if not lines or not lines[0].upper().startswith("OPENQASM 2.0"):
            raise ValueError("QASM string must start with 'OPENQASM 2.0;'")

        num_qubits = 0
        parsed_gates: List[QuantumGate] = []

        for line in lines:
            if line.startswith("qreg"):
                try:
                    # Example: qreg q[5];
                    size_str = line.split('[')[1].split(']')[0]
                    num_qubits = max(num_qubits, int(size_str))
                except (IndexError, ValueError):
                    raise ValueError(f"Could not parse qreg definition: {line}")
                continue
            
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue

            # Basic gate parsing
            parts = line.split(";") # Remove semicolon
            if not parts[0]: continue
            
            command_args = parts[0].split(maxsplit=1)
            gate_type_qasm = command_args[0]
            
            if not command_args[1:]: # Should not happen if line is valid QASM gate
                raise ValueError(f"Malformed gate instruction: {line}")

            args_str = command_args[1]
            
            # Parse parameters like rx(pi/2) q[0];
            params: Optional[List[float]] = None
            if '(' in gate_type_qasm and ')' in gate_type_qasm:
                param_content = gate_type_qasm[gate_type_qasm.find('(')+1 : gate_type_qasm.rfind(')')]
                try:
                    # Handle simple expressions like pi/2, but not full eval
                    # For safety, this parser should be very restricted or use a proper QASM library
                    # For now, only float parameters are supported
                    param_values_str = param_content.split(',')
                    params = []
                    for p_str in param_values_str:
                        if p_str.lower() == "pi": params.append(3.1415926535) # Approximate pi
                        elif "pi/" in p_str.lower():
                            try:
                                divisor = float(p_str.lower().split("pi/")[1])
                                params.append(3.1415926535 / divisor)
                            except ValueError:
                                raise ValueError(f"Cannot parse parameter expression: {p_str} in {line}")
                        else:
                            params.append(float(p_str))

                except ValueError:
                    raise ValueError(f"Could not parse parameters for gate {gate_type_qasm}: {param_content}")
                gate_type_qasm = gate_type_qasm.split('(')[0] # Get base gate type

            # Parse qubit arguments like q[0], q[1]
            qubit_indices: List[int] = []
            try:
                # Assumes qubits are specified like q[idx] or q[idx],q[jdx]
                # More robust parsing needed for complex register handling
                raw_qubit_args = args_str.split(',')
                for raw_arg in raw_qubit_args:
                    arg_clean = raw_arg.strip()
                    if arg_clean.startswith("q[") and arg_clean.endswith("]"):
                        qubit_indices.append(int(arg_clean[2:-1]))
                    else: # Could be other register types, not supported by this simple parser
                        raise ValueError(f"Unsupported qubit argument format: {arg_clean} in {line}")
            except (IndexError, ValueError):
                raise ValueError(f"Could not parse qubit arguments for gate: {line}")

            if not qubit_indices:
                raise ValueError(f"No qubit arguments found for gate: {line}")

            # Map QASM gate names to Orquestra SDK gate types (can be extended)
            gate_type_sdk = gate_type_qasm.upper()
            if gate_type_sdk == "CX": gate_type_sdk = "CNOT"
            # Add more mappings if QASM names differ from internal SDK names

            parsed_gates.append(QuantumGate(
                type=gate_type_sdk,
                qubits=qubit_indices,
                parameters=params
            ))

        if num_qubits == 0 and parsed_gates: # Infer from max qubit index if no qreg
            max_idx = -1
            for g in parsed_gates:
                max_idx = max(max_idx, *g.qubits)
            num_qubits = max_idx + 1
        elif num_qubits == 0 and not parsed_gates: # Empty circuit
            num_qubits = 1 # Default to 1 qubit for an empty circuit if qreg is missing

        return cls(
            id=circuit_id or str(uuid4()),
            name=name or "Circuit from QASM",
            qubits=num_qubits,
            gates=parsed_gates
        )

    def copy(self: QC, deep: bool = True) -> QC:
        """
        Creates a copy of this quantum circuit.

        Args:
            deep (bool): If True, performs a deep copy of the gates and metadata.
                         If False, performs a shallow copy (gates and metadata are references).

        Returns:
            QuantumCircuit: A new QuantumCircuit instance.
        """
        if deep:
            new_gates = [gate.copy(deep=True) for gate in self.gates]
            new_metadata = self.metadata.copy() if self.metadata else None
        else:
            new_gates = self.gates[:] # Shallow copy of the list
            new_metadata = self.metadata # Reference
        
        return self.__class__(
            id=str(uuid4()), # New ID for the new circuit
            name=f"{self.name} (Copy)",
            qubits=self.qubits,
            gates=new_gates,
            metadata=new_metadata
        )

    def append(
        self: QC, 
        other_circuit: "QuantumCircuit", 
        qubit_mapping: Optional[Dict[int, int]] = None
    ) -> None:
        """
        Appends another circuit to this one. Gates from the other circuit are added
        to the end of this circuit's gate list.

        Args:
            other_circuit (QuantumCircuit): The circuit to append.
            qubit_mapping (Optional[Dict[int, int]]):
                A dictionary mapping logical qubit indices from `other_circuit`
                to logical qubit indices in `self`.
                For example, `{0: self.qubits, 1: self.qubits + 1}` would append
                `other_circuit` starting on new qubits after `self`'s current qubits.
                If None, assumes `other_circuit` acts on the same qubit indices
                (0 to `other_circuit.qubits - 1`), which must be within `self.qubits` range.

        Raises:
            ValueError: If qubit mapping is invalid or results in out-of-bounds qubit indices.
                        Or if appending results in duplicate gate IDs.
        """
        new_gates_to_add: List[QuantumGate] = []
        
        # Determine the maximum qubit index required if appending
        max_target_qubit_idx = self.qubits -1
        if qubit_mapping:
            for source_idx, target_idx in qubit_mapping.items():
                if not (0 <= source_idx < other_circuit.qubits):
                    raise ValueError(f"Invalid source qubit index {source_idx} in qubit_mapping. "
                                     f"Other circuit has {other_circuit.qubits} qubits.")
                max_target_qubit_idx = max(max_target_qubit_idx, target_idx)
        else:
            # If no mapping, other_circuit acts on its own qubit indices within self
            if other_circuit.qubits > self.qubits:
                 raise ValueError(f"Cannot append circuit with {other_circuit.qubits} qubits to circuit with "
                                  f"{self.qubits} qubits without a qubit_mapping that fits.")
            max_target_qubit_idx = max(max_target_qubit_idx, other_circuit.qubits -1)


        # If the appended circuit requires more qubits than self currently has,
        # and a mapping is provided that implies this, we might need to increase self.qubits.
        # For now, let's assume self.qubits must be large enough for the mapping.
        # A more advanced version could auto-expand self.qubits.
        if max_target_qubit_idx >= self.qubits:
            # This logic could be to expand self.qubits, but for now, let's error
            # if the mapping implies out-of-bounds for the *current* self.qubits.
            # The user should expand self.qubits explicitly if that's the intent,
            # or the mapping should map to existing qubits.
            # For simplicity, let's stick to the current self.qubits limit.
            # If a mapping goes beyond, it's an error.
            # A more robust `compose` or `tensor` method might handle qubit expansion.
            pass # Validation for mapped qubits being < self.qubits will happen in add_gates


        for gate_to_append in other_circuit.gates:
            new_gate = gate_to_append.copy(deep=True)
            new_gate.id = str(uuid4()) # Ensure unique ID for the appended gate

            mapped_qubits: List[int] = []
            if qubit_mapping:
                for q_idx in gate_to_append.qubits:
                    if q_idx not in qubit_mapping:
                        raise ValueError(f"Qubit {q_idx} from appended circuit's gate {gate_to_append.id} "
                                         "is not found in the provided qubit_mapping.")
                    mapped_qubits.append(qubit_mapping[q_idx])
            else: # No mapping, direct qubit indices
                mapped_qubits = gate_to_append.qubits[:]
            
            new_gate.qubits = mapped_qubits
            new_gates_to_add.append(new_gate)
            
        # This will perform validation including qubit bounds and ID uniqueness
        self.add_gates(new_gates_to_add)


    class Config:
        validate_assignment = True
        frozen = False # Allow modification of gates list, etc.

# Example Usage (can be removed or moved to tests/examples)
if __name__ == "__main__":
    # Gate examples
    h_gate = QuantumGate(type="H", qubits=[0])
    cx_gate = QuantumGate(type="CNOT", qubits=[0, 1])
    rx_gate = QuantumGate(type="RX", qubits=[0], parameters=[1.5708]) # pi/2
    
    print(h_gate)
    print(repr(cx_gate))

    # Circuit examples
    bell_circuit = QuantumCircuit(name="Bell State", qubits=2)
    bell_circuit.add_gate(h_gate)
    bell_circuit.add_gate(cx_gate)

    print(bell_circuit)
    print(f"Bell Circuit Depth: {bell_circuit.depth()}")
    print(f"Bell Circuit Gate Counts: {bell_circuit.gate_counts()}")
    print(f"Bell Circuit QASM:\n{bell_circuit.to_qasm()}")

    # Test validation
    try:
        invalid_gate = QuantumGate(type="X", qubits=[2]) # Qubit out of bounds for bell_circuit
        bell_circuit.add_gate(invalid_gate)
    except ValueError as e:
        print(f"\nCaught expected error: {e}")

    try:
        # Adding gate with duplicate ID
        bell_circuit.add_gate(QuantumGate(id=h_gate.id, type="Z", qubits=[1]))
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Test copy
    bell_copy = bell_circuit.copy()
    bell_copy.name = "Bell State Copy"
    bell_copy.add_gate(QuantumGate(type="Z", qubits=[0])) # Modify copy
    print(f"\nOriginal Bell Circuit: {bell_circuit.name}, Gates: {len(bell_circuit)}")
    print(f"Copied Bell Circuit: {bell_copy.name}, Gates: {len(bell_copy)}")

    # Test append
    ghz_part = QuantumCircuit(name="GHZ Extension", qubits=2, gates=[
        QuantumGate(type="CNOT", qubits=[0,1]) # Logically, this is qubit 0 and 1 of ghz_part
    ])
    
    # Append ghz_part to bell_copy, mapping ghz_part's q0 to bell_copy's q1, and ghz_part's q1 to a new qubit (q2 of bell_copy)
    # First, ensure bell_copy has enough qubits for the mapping
    bell_copy_original_qubits = bell_copy.qubits
    required_qubits_for_append = 3 
    if bell_copy.qubits < required_qubits_for_append:
        bell_copy.qubits = required_qubits_for_append # Manually expand for this example
        print(f"Expanded '{bell_copy.name}' to {bell_copy.qubits} qubits for append operation.")

    # Mapping: other_circuit_qubit_idx -> self_circuit_qubit_idx
    # ghz_part q0 -> bell_copy q1
    # ghz_part q1 -> bell_copy q2
    mapping = {0: 1, 1: 2} 
    
    try:
        bell_copy.append(ghz_part, qubit_mapping=mapping)
        print(f"\nAppended circuit: {bell_copy.name}, Gates: {len(bell_copy)}")
        print(f"Appended circuit QASM:\n{bell_copy.to_qasm()}")
    except ValueError as e:
        print(f"Error during append: {e}")
        # Reset qubit count if append failed due to qubit expansion logic (if it were more complex)
        bell_copy.qubits = bell_copy_original_qubits


    # QASM from_qasm example
    qasm_str_example = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    h q[0];
    cx q[0],q[1];
    rx(pi/4) q[2];
    """
    try:
        parsed_circuit = QuantumCircuit.from_qasm(qasm_str_example, name="Parsed GHZ-like")
        print(f"\nParsed circuit: {parsed_circuit.name}")
        print(f"Qubits: {parsed_circuit.qubits}")
        print(f"Gates: {parsed_circuit.gates}")
        print(f"Depth: {parsed_circuit.depth()}")
        print(f"QASM output:\n{parsed_circuit.to_qasm()}")
    except ValueError as e:
        print(f"Error parsing QASM: {e}")

    # Example of a more complex circuit for depth calculation
    complex_circuit = QuantumCircuit(name="Complex Test", qubits=4)
    complex_circuit.add_gates([
        QuantumGate(type="H", qubits=[0]), QuantumGate(type="H", qubits=[1]), QuantumGate(type="H", qubits=[2]), QuantumGate(type="H", qubits=[3]), # Layer 1
        QuantumGate(type="CNOT", qubits=[0,1]), QuantumGate(type="CNOT", qubits=[2,3]), # Layer 2
        QuantumGate(type="X", qubits=[0]), QuantumGate(type="Z", qubits=[2]), # Layer 3
        QuantumGate(type="CNOT", qubits=[1,2]), # Layer 4 (waits for q1 from L2, q2 from L3)
        QuantumGate(type="H", qubits=[1]), QuantumGate(type="H", qubits=[2]), # Layer 5
    ])
    print(f"\n{complex_circuit.name} Depth: {complex_circuit.depth()}") # Expected: 5
    # Layer 1: H q[0], H q[1], H q[2], H q[3] -> qf = [1,1,1,1]
    # Layer 2: CNOT q[0],q[1]; CNOT q[2],q[3] -> qf for q0,q1 is 2; qf for q2,q3 is 2. Overall qf = [2,2,2,2]
    # Layer 3: X q[0]; Z q[2] -> qf for q0 is 3; qf for q2 is 3. Overall qf = [3,2,3,2]
    # Layer 4: CNOT q[1],q[2]. q1 finishes at L2, q2 finishes at L3. Gate starts at max(2,3)=3. Finishes at L4.
    #          qf for q1 is 4; qf for q2 is 4. Overall qf = [3,4,4,2]
    # Layer 5: H q[1]; H q[2]. q1 finishes at L4, q2 finishes at L4. Gates start at max(4,4)=4. Finish at L5.
    #          qf for q1 is 5; qf for q2 is 5. Overall qf = [3,5,5,2]. Max depth = 5. Correct.
