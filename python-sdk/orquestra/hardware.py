"""
Orquestra SDK: Quantum Hardware Architecture Definitions
-------------------------------------------------------

This module defines Pydantic models for representing the architecture and
characteristics of quantum hardware devices. These models are crucial for
performing realistic quantum resource estimations.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, model_validator, field_validator, ValidationInfo

# Import Literal for type hinting, ensuring compatibility
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

class ConnectivityType(str, Enum):
    """
    Defines the types of qubit connectivity patterns in a quantum device.
    """
    ALL_TO_ALL = "all-to-all"
    LINEAR = "linear"
    RING = "ring"
    GRID = "grid" # Assumes a square-ish grid, specific dimensions might be inferred or specified
    HEAVY_HEX = "heavy-hex" # e.g., IBM's heavy-hex lattice
    HEAVY_SQUARE = "heavy-square" # e.g., Rigetti's Aspen-M like lattice
    CUSTOM = "custom" # Connectivity defined by an explicit adjacency list/matrix

class CustomConnectivityModel(BaseModel):
    """
    Model for defining custom qubit connectivity using an adjacency list.
    """
    type: Literal[ConnectivityType.CUSTOM] = Field(default=ConnectivityType.CUSTOM, frozen=True)
    adjacencies: List[List[int]] = Field(
        ...,
        description="Adjacency list where adjacencies[i] is a list of qubits connected to qubit i."
    )

    @field_validator('adjacencies')
    @classmethod
    def check_adjacency_list_symmetry_and_bounds(cls, v: List[List[int]]) -> List[List[int]]:
        """
        Validates the adjacency list for symmetry (undirected graph) and ensures
        indices are within bounds. The number of qubits is inferred from len(v).
        """
        num_qubits = len(v)
        for i in range(num_qubits):
            for neighbor in v[i]:
                if not (0 <= neighbor < num_qubits):
                    raise ValueError(f"Qubit index {neighbor} in adjacency list for qubit {i} "
                                     f"is out of bounds for {num_qubits} qubits (derived from list length).")
                if i not in v[neighbor]: # Check symmetry
                    raise ValueError(f"Asymmetric connection: qubit {i} connects to {neighbor}, "
                                     f"but {neighbor} does not connect back to {i}.")
        return v

class GateErrorModel(BaseModel):
    """
    Defines error rates for various gate types.
    Special keys 'single_qubit' and 'two_qubit' can be used for average error rates.
    Specific gate types (e.g., "H", "CNOT") override these averages if provided.
    Error rates are probabilities (0.0 to 1.0).
    """
    single_qubit: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Average error rate for any single-qubit gate.")
    two_qubit: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Average error rate for any two-qubit gate.")

    model_config = {"extra": "allow"}

    @model_validator(mode='after')
    def check_all_error_rates_are_valid(self) -> 'GateErrorModel':
        # model_dump() includes explicitly set fields and extra fields.
        for gate_type, error_rate in self.model_dump(exclude_none=True, by_alias=False).items(): # by_alias=False for original field names
            if not isinstance(error_rate, (float, int)):
                 raise ValueError(f"Error rate for gate type '{gate_type}' must be a number. Got {type(error_rate)}.")
            if not (0.0 <= float(error_rate) <= 1.0):
                raise ValueError(f"Error rate for gate type '{gate_type}' ({error_rate}) must be between 0.0 and 1.0.")
        return self

class GateTimingsModel(BaseModel):
    """
    Defines execution durations for various gate types in nanoseconds (ns).
    Special keys 'single_qubit', 'two_qubit', and 'measurement' can be used for averages.
    Specific gate types override these. Durations must be positive.
    """
    single_qubit: Optional[float] = Field(default=None, gt=0, description="Average duration for any single-qubit gate (ns).")
    two_qubit: Optional[float] = Field(default=None, gt=0, description="Average duration for any two-qubit gate (ns).")
    measurement: Optional[float] = Field(default=None, gt=0, description="Average duration for a qubit measurement operation (ns).")

    model_config = {"extra": "allow"}

    @model_validator(mode='after')
    def check_all_timings_are_positive(self) -> 'GateTimingsModel':
        for gate_type, duration in self.model_dump(exclude_none=True, by_alias=False).items():
            if not isinstance(duration, (float, int)):
                 raise ValueError(f"Duration for gate type '{gate_type}' must be a number. Got {type(duration)}.")
            if float(duration) <= 0:
                raise ValueError(f"Duration for gate type '{gate_type}' ({duration}) must be positive.")
        return self

class HardwareConstraintsModel(BaseModel):
    """
    Defines operational constraints of the quantum hardware.
    """
    max_circuit_depth: Optional[int] = Field(default=None, gt=0, description="Maximum circuit depth supported by the hardware.")
    max_shots: Optional[int] = Field(default=None, gt=0, description="Maximum number of shots allowed per execution.")

class QuantumHardwareArchitecture(BaseModel):
    """
    Represents the detailed architecture and characteristics of a quantum hardware device.
    This model is crucial for realistic quantum resource estimation.
    """
    name: str = Field(..., description="Name of the quantum processor or architecture (e.g., 'IBM Eagle R1', 'Google Sycamore').")
    qubit_count: int = Field(..., gt=0, description="Total number of available physical qubits.")
    connectivity: Union[ConnectivityType, CustomConnectivityModel] = Field(
        ...,
        description="Qubit interaction topology. Can be a predefined type or a custom adjacency list."
    )
    native_gate_set: List[str] = Field(
        ...,
        min_length=1, # Must have at least one native gate
        description="List of gate types natively supported by the hardware (e.g., ['X', 'RZ', 'ECR']). Case-insensitive during validation, stored as uppercase."
    )
    gate_errors: GateErrorModel = Field(
        ...,
        description="Error rates per native gate type or generic types."
    )
    readout_errors: Union[List[float], float] = Field(
        ...,
        description="Readout error rates. Either a list of per-qubit rates or a single average rate for all qubits. Values are probabilities (0.0 to 1.0)."
    )
    t1_times: Union[List[float], float] = Field(
        ...,
        description="T1 relaxation times in microseconds (µs). Either a list of per-qubit T1 times or a single average T1 time."
    )
    t2_times: Union[List[float], float] = Field(
        ...,
        description="T2 dephasing/coherence times in microseconds (µs). Either a list of per-qubit T2 times or a single average T2 time."
    )
    gate_timings: GateTimingsModel = Field(
        ...,
        description="Average duration (in nanoseconds, ns) per native gate type or generic types."
    )
    crosstalk_matrix: Optional[List[List[float]]] = Field(
        default=None,
        description="Optional N x N matrix describing crosstalk error probabilities between pairs of qubits, where N is qubit_count. crosstalk_matrix[i][j] is the probability of an error on qubit i due to an operation on qubit j."
    )
    constraints: Optional[HardwareConstraintsModel] = Field(
        default=None,
        description="Optional operational constraints of the hardware."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary for additional vendor-specific or descriptive information."
    )

    @field_validator('native_gate_set', mode='before')
    @classmethod
    def uppercase_native_gates(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            raise TypeError("Native gate set must be a list.")
        processed_list = []
        for item in v:
            if not isinstance(item, str):
                raise TypeError("Native gate set items must be strings.")
            processed_list.append(item.upper())
        return processed_list

    @field_validator('native_gate_set')
    @classmethod
    def check_native_gate_set_unique_and_not_empty(cls, v: List[str]) -> List[str]:
        if not v: # Should be caught by min_length=1, but good to have.
            raise ValueError("Native gate set must not be empty.")
        if len(v) != len(set(v)):
            raise ValueError("Native gate set must contain unique gate types.")
        return v

    @field_validator('gate_errors')
    @classmethod
    def validate_gate_error_keys(cls, v: GateErrorModel, info: ValidationInfo) -> GateErrorModel:
        if 'native_gate_set' not in info.data: # Should not happen if native_gate_set is required and validated first
            raise ValueError("Cannot validate gate_errors: native_gate_set not available in validation context.")
        native_gates = set(info.data['native_gate_set']) # Already uppercased
        allowed_generic_keys = {"single_qubit", "two_qubit"}

        # Check extra fields in GateErrorModel against native_gate_set
        # model_extra is available in Pydantic v2 for fields not explicitly defined
        for gate_type_key in v.model_extra if v.model_extra else {}:
            if gate_type_key.upper() not in native_gates:
                 raise ValueError(
                    f"Extra gate type '{gate_type_key}' in gate_errors is not in native_gate_set "
                    f"({list(native_gates)})."
                )
        return v

    @field_validator('gate_timings')
    @classmethod
    def validate_gate_timing_keys(cls, v: GateTimingsModel, info: ValidationInfo) -> GateTimingsModel:
        if 'native_gate_set' not in info.data:
             raise ValueError("Cannot validate gate_timings: native_gate_set not available in validation context.")
        native_gates = set(info.data['native_gate_set']) # Already uppercased
        allowed_generic_keys = {"single_qubit", "two_qubit", "measurement"}

        for gate_type_key in v.model_extra if v.model_extra else {}:
            if gate_type_key.upper() not in native_gates:
                raise ValueError(
                    f"Extra gate type '{gate_type_key}' in gate_timings is not in native_gate_set "
                    f"({list(native_gates)})."
                )
        return v
        
    @field_validator('readout_errors')
    @classmethod
    def validate_readout_errors_format(cls, v: Union[List[float], float], info: ValidationInfo) -> Union[List[float], float]:
        # This validator runs after Pydantic attempts to coerce v.
        # We primarily check consistency with qubit_count.
        qubit_count = info.data.get('qubit_count')
        if qubit_count is None: # Should be validated by now
            return v 

        if isinstance(v, list):
            if len(v) != qubit_count:
                raise ValueError(f"Length of readout_errors list ({len(v)}) must match qubit_count ({qubit_count}).")
            # Positivity/range is handled by GateErrorModel's field definition (ge=0, le=1)
            # Pydantic v2 handles per-item validation in List[float] if item type has constraints
        # else: float/int scalar, range handled by field definition
        return v

    @field_validator('t1_times', 't2_times')
    @classmethod
    def validate_coherence_times_format(cls, v: Union[List[float], float], info: ValidationInfo) -> Union[List[float], float]:
        qubit_count = info.data.get('qubit_count')
        field_name = info.field_name
        if qubit_count is None:
            return v

        if isinstance(v, list):
            if len(v) != qubit_count:
                raise ValueError(f"Length of {field_name} list ({len(v)}) must match qubit_count ({qubit_count}).")
            # Positivity is handled by GateTimingsModel's field definition (gt=0)
        # else: float/int scalar, positivity handled by field definition
        return v

    @model_validator(mode='after')
    def check_custom_connectivity_with_qubit_count(self) -> 'QuantumHardwareArchitecture':
        if isinstance(self.connectivity, CustomConnectivityModel):
            if self.qubit_count != len(self.connectivity.adjacencies): # qubit_count is now validated
                raise ValueError(
                    f"Length of custom connectivity adjacency list ({len(self.connectivity.adjacencies)}) "
                    f"must match qubit_count ({self.qubit_count})."
                )
        return self

    @model_validator(mode='after')
    def check_t2_less_than_or_equal_to_2t1_model_level(self) -> 'QuantumHardwareArchitecture':
        # All fields are validated at this point
        t1_val = self.t1_times
        t2_val = self.t2_times
        
        t1_list = [float(t1_val)] * self.qubit_count if isinstance(t1_val, (float, int)) else [float(x) for x in t1_val]
        t2_list = [float(t2_val)] * self.qubit_count if isinstance(t2_val, (float, int)) else [float(x) for x in t2_val]

        for i in range(self.qubit_count):
            if t2_list[i] > (2 * t1_list[i]) + 1e-9: # Add tolerance for float comparison
                raise ValueError(
                    f"T2 time for qubit {i} ({t2_list[i]} µs) cannot significantly exceed 2 * T1 time ({2 * t1_list[i]} µs)."
                )
        return self

    @field_validator('crosstalk_matrix')
    @classmethod
    def validate_crosstalk_matrix_format(cls, v: Optional[List[List[float]]], info: ValidationInfo) -> Optional[List[List[float]]]:
        if v is None:
            return None
        
        qubit_count = info.data.get('qubit_count')
        if qubit_count is None:
            raise ValueError("Cannot validate crosstalk_matrix: qubit_count is not available in validation context.")

        if len(v) != qubit_count:
            raise ValueError(f"Crosstalk matrix must have {qubit_count} rows (found {len(v)}).")
        
        for i, row in enumerate(v):
            if len(row) != qubit_count:
                raise ValueError(f"Row {i} of crosstalk matrix must have {qubit_count} columns (found {len(row)}).")
            for j, val_element in enumerate(row):
                if not (0.0 <= float(val_element) <= 1.0):
                    raise ValueError(f"Crosstalk matrix element ({i},{j}) value {val_element} must be between 0.0 and 1.0.")
                if i == j and abs(float(val_element)) > 1e-9 :
                    pass 
        return v
        
    def get_gate_error(self, gate_type: str, num_qubits_acted_on: int) -> float:
        """
        Retrieves the error rate for a given gate type, considering generic fallbacks.
        """
        errors_data = self.gate_errors.model_dump(exclude_none=True, by_alias=False)
        gate_type_upper = gate_type.upper()

        # 1. Check for specific gate type (user-defined keys are case-sensitive as provided)
        #    Native gates are stored uppercase, so we check uppercase first.
        if gate_type_upper in errors_data:
            return float(errors_data[gate_type_upper])
        # Check original case if it was an "extra" field not matching a native gate's uppercase
        if gate_type in errors_data: # For model_extra fields that might not be uppercased
            return float(errors_data[gate_type])
        
        # 2. Fallback to generic types (these are defined fields, not from model_extra)
        if num_qubits_acted_on == 1 and self.gate_errors.single_qubit is not None:
            return self.gate_errors.single_qubit
        if num_qubits_acted_on >= 2 and self.gate_errors.two_qubit is not None:
            return self.gate_errors.two_qubit
        
        # from . import logger # Assuming logger is defined in __init__.py
        # logger.warning(f"No error rate found for gate type '{gate_type}' or generic {num_qubits_acted_on}-qubit type. Using default high error.")
        return 0.1 # Default high error rate

    def get_gate_timing(self, gate_type: str, num_qubits_acted_on: int) -> float:
        """
        Retrieves the duration for a given gate type, considering generic fallbacks.
        """
        timings_data = self.gate_timings.model_dump(exclude_none=True, by_alias=False)
        gate_type_upper = gate_type.upper()

        if gate_type_upper in timings_data:
            return float(timings_data[gate_type_upper])
        if gate_type in timings_data: # For model_extra fields
            return float(timings_data[gate_type])

        if gate_type.upper() == 'MEASUREMENT' and self.gate_timings.measurement is not None:
            return self.gate_timings.measurement
        if num_qubits_acted_on == 1 and self.gate_timings.single_qubit is not None:
            return self.gate_timings.single_qubit
        if num_qubits_acted_on >= 2 and self.gate_timings.two_qubit is not None:
            return self.gate_timings.two_qubit

        # from . import logger
        # logger.warning(f"No timing found for gate type '{gate_type}' or generic {num_qubits_acted_on}-qubit type. Using default high duration.")
        return 1000.0 # Default high duration (ns)

    def get_readout_error(self, qubit_index: int) -> float:
        """Retrieves the readout error for a specific qubit."""
        if not (0 <= qubit_index < self.qubit_count):
            raise IndexError(f"Qubit index {qubit_index} out of range for hardware with {self.qubit_count} qubits.")
        if isinstance(self.readout_errors, (float, int)):
            return float(self.readout_errors)
        return float(self.readout_errors[qubit_index])

    def get_t1_time(self, qubit_index: int) -> float:
        """Retrieves the T1 time for a specific qubit."""
        if not (0 <= qubit_index < self.qubit_count):
            raise IndexError(f"Qubit index {qubit_index} out of range for hardware with {self.qubit_count} qubits.")
        if isinstance(self.t1_times, (float, int)):
            return float(self.t1_times)
        return float(self.t1_times[qubit_index])

    def get_t2_time(self, qubit_index: int) -> float:
        """Retrieves the T2 time for a specific qubit."""
        if not (0 <= qubit_index < self.qubit_count):
            raise IndexError(f"Qubit index {qubit_index} out of range for hardware with {self.qubit_count} qubits.")
        if isinstance(self.t2_times, (float, int)):
            return float(self.t2_times)
        return float(self.t2_times[qubit_index])

    class Config:
        validate_assignment = True

# Example Usage (can be removed or moved to tests/examples)
if __name__ == "__main__":
    # Example of a simple hardware architecture
    basic_linear_arch = QuantumHardwareArchitecture(
        name="Basic Linear 3Q",
        qubit_count=3,
        connectivity=ConnectivityType.LINEAR,
        native_gate_set=["X", "H", "RZ", "CNOT"],
        gate_errors={"single_qubit": 0.001, "CNOT": 0.01, "X": 0.0005}, # Pass as dict
        readout_errors=0.02, # Average
        t1_times=[100.0, 110.0, 105.0], # Per-qubit
        t2_times=80.0, # Average
        gate_timings={"single_qubit": 50, "CNOT": 300, "measurement": 1000} # Pass as dict
    )
    print("Basic Linear Architecture:")
    print(basic_linear_arch.model_dump_json(indent=2))
    print(f"  Error for X gate: {basic_linear_arch.get_gate_error('X', 1)}")
    print(f"  Error for H gate (fallback to single-qubit): {basic_linear_arch.get_gate_error('H', 1)}")
    print(f"  T1 for qubit 1: {basic_linear_arch.get_t1_time(1)}")

    # Example of custom connectivity
    custom_connectivity_data = CustomConnectivityModel(
        adjacencies=[
            [1],    # Q0 connected to Q1
            [0, 2], # Q1 connected to Q0, Q2
            [1]     # Q2 connected to Q1
        ]
    )
    
    advanced_arch_data = {
        "name": "Advanced Custom 3Q",
        "qubit_count": 3,
        "connectivity": custom_connectivity_data.model_dump(), # Pass as dict
        "native_gate_set": ["U3", "CX"],
        "gate_errors": {"U3": 0.0007, "CX": 0.006, "single_qubit": 0.001}, # Pass as dict
        "readout_errors": [0.01, 0.012, 0.009],
        "t1_times": 150.0,
        "t2_times": 120.0,
        "gate_timings": {"U3": 40, "CX": 250, "measurement": 800, "single_qubit": 50}, # Pass as dict
        "crosstalk_matrix": [
            [0.0, 0.001, 0.0005],
            [0.001, 0.0, 0.0015],
            [0.0005, 0.0015, 0.0]
        ],
        "constraints": {"max_shots":10000, "max_circuit_depth":5000} # Pass as dict
    }
    advanced_arch = QuantumHardwareArchitecture(**advanced_arch_data)
    print("\nAdvanced Custom Architecture:")
    print(advanced_arch.model_dump_json(indent=2))

    # Test validation errors
    try:
        invalid_arch = QuantumHardwareArchitecture(
            name="Invalid Arch",
            qubit_count=2,
            connectivity=ConnectivityType.LINEAR,
            native_gate_set=["X"],
            gate_errors={"Y": 0.1}, # Y not in native_gate_set
            readout_errors=0.01,
            t1_times=100,
            t2_times=50,
            gate_timings={"X": 10}
        )
    except ValueError as e:
        print(f"\nCaught expected validation error: {e}")

    try:
        invalid_t2 = QuantumHardwareArchitecture(
            name="Invalid T2",
            qubit_count=1,
            connectivity=ConnectivityType.LINEAR, 
            native_gate_set=["X"],
            gate_errors={"X": 0.001},
            readout_errors=0.01,
            t1_times=50,
            t2_times=110, # T2 > 2 * T1
            gate_timings={"X": 10}
        )
    except ValueError as e:
        print(f"\nCaught expected validation error for T2 vs T1: {e}")

    try:
        invalid_custom_conn = QuantumHardwareArchitecture(
            name="Invalid Custom Conn",
            qubit_count=2,
            connectivity={"type": "custom", "adjacencies": [[1],[0],[0]]}, # 3 rows for 2 qubits
            native_gate_set=["X"],
            gate_errors={"X": 0.001}, readout_errors=0.01, t1_times=100, t2_times=50, gate_timings={"X": 10}
        )
    except ValueError as e:
        print(f"\nCaught expected validation error for custom connectivity: {e}")
