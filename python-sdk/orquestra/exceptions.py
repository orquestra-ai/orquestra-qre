"""
Orquestra SDK: Custom Exceptions
--------------------------------

This module defines a hierarchy of custom exceptions used throughout the
Orquestra Python SDK. These exceptions provide more specific error information
than built-in Python exceptions, aiding in debugging and error handling.
"""

class OrquestraSDKError(Exception):
    """
    Base class for all custom exceptions raised by the Orquestra SDK.

    Catching this exception will catch any error originating specifically
    from the Orquestra SDK.
    """
    def __init__(self, message: str, original_exception: Exception = None): # type: ignore
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self) -> str:
        if self.original_exception:
            return f"{self.message}: {self.original_exception}"
        return self.message

class CircuitValidationError(OrquestraSDKError):
    """
    Raised when there is an issue with the definition or validation of a
    QuantumCircuit object.

    Examples:
        - A gate acts on qubit indices outside the circuit's defined range.
        - Duplicate gate IDs within a circuit.
        - Malformed QASM input during parsing.
    """
    pass

class HardwareDefinitionError(OrquestraSDKError):
    """
    Raised when there is an issue with the definition or validation of a
    QuantumHardwareArchitecture object.

    Examples:
        - Inconsistent qubit counts between different hardware parameters.
        - Invalid error rates or timings (e.g., negative values, T2 > 2*T1).
        - Gate types in error/timing models not matching the native gate set.
        - Malformed custom connectivity definitions.
    """
    pass

class EstimationError(OrquestraSDKError):
    """
    Raised when an error occurs during the quantum resource estimation process.

    This could be due to various reasons, such as:
        - Inability to estimate resources for a given circuit-architecture pair
          (e.g., circuit too large for architecture).
        - Mathematical errors or inconsistencies encountered during calculations.
        - Unsupported features or configurations requested for estimation.
    """
    pass

class ProviderIntegrationError(OrquestraSDKError):
    """
    Raised when an error occurs during interaction or integration with an
    external quantum hardware provider's SDK or API.

    This typically involves issues with:
        - Authentication or authorization with the provider.
        - Submitting jobs or querying provider status.
        - Translating Orquestra circuit/hardware models to provider-specific formats.
        - Unexpected responses or errors from the provider's systems.
    """
    pass

class ConfigurationError(OrquestraSDKError):
    """
    Raised when there is an issue with the SDK's configuration or
    the configuration provided by the user.

    Examples:
        - Missing required configuration parameters.
        - Invalid values for configuration settings.
        - Issues loading or parsing configuration files.
    """
    pass

class NotImplementedFeatureError(OrquestraSDKError):
    """
    Raised when a feature or functionality is called but has not yet
    been implemented in the SDK.
    """
    def __init__(self, feature_name: str):
        super().__init__(f"The feature '{feature_name}' is not yet implemented in the Orquestra SDK.")
        self.feature_name = feature_name

class QASMImportError(CircuitValidationError):
    """
    Raised specifically when parsing a QASM string into a QuantumCircuit fails.
    Inherits from CircuitValidationError.
    """
    def __init__(self, message: str, qasm_line: int = None, qasm_content: str = None): # type: ignore
        full_message = f"Error parsing QASM: {message}"
        if qasm_line is not None:
            full_message += f" (at or near line {qasm_line})"
        if qasm_content:
            # For brevity, might only show a snippet around the error if content is long
            snippet_radius = 30
            content_snippet = qasm_content
            if len(qasm_content) > snippet_radius * 2 + 10: # If content is long
                start = max(0, len(qasm_content)//2 - snippet_radius) # Rough middle
                end = min(len(qasm_content), len(qasm_content)//2 + snippet_radius)
                content_snippet = f"...{qasm_content[start:end]}..."

            full_message += f"\nContent snippet: '{content_snippet}'"

        super().__init__(full_message)
        self.qasm_line = qasm_line
        self.qasm_content = qasm_content


# Example of how these might be used (for illustration, not part of the module itself):
if __name__ == "__main__":
    def simulate_error(error_type: str):
        if error_type == "circuit":
            raise CircuitValidationError("Invalid gate qubit index: 5 (max qubits: 3).")
        elif error_type == "hardware":
            raise HardwareDefinitionError("T2 time (150us) exceeds 2*T1 time (2*50us=100us) for qubit 0.")
        elif error_type == "estimation":
            raise EstimationError("Cannot estimate Quantum Volume: physical error rate exceeds threshold.")
        elif error_type == "provider":
            original_api_error = ConnectionError("Failed to connect to provider API endpoint.")
            raise ProviderIntegrationError("IBM provider API request failed", original_exception=original_api_error)
        elif error_type == "config":
            raise ConfigurationError("Missing API key for 'XYZ_PROVIDER_TOKEN'.")
        elif error_type == "not_implemented":
            raise NotImplementedFeatureError("Advanced tensor network simulation")
        elif error_type == "qasm":
            qasm_example = "OPENQASM 2.0;\nqreg q[2];\ninvalid_gate q[0];"
            raise QASMImportError("Unknown gate 'invalid_gate'", qasm_line=3, qasm_content="invalid_gate q[0];")
        else:
            print("Unknown error type for simulation.")

    error_types_to_test = ["circuit", "hardware", "estimation", "provider", "config", "not_implemented", "qasm"]
    for etype in error_types_to_test:
        try:
            print(f"\nSimulating '{etype}' error...")
            simulate_error(etype)
        except OrquestraSDKError as e:
            print(f"Caught OrquestraSDKError: {e.__class__.__name__}")
            print(f"  Message: {e}")
            if hasattr(e, 'original_exception') and e.original_exception: # type: ignore
                print(f"  Original Exception: {e.original_exception.__class__.__name__} - {e.original_exception}") # type: ignore
        except Exception as e_generic:
            print(f"Caught unexpected generic error: {e_generic}")
```
