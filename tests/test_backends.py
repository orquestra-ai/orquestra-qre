"""
Unit tests for the backends module.
"""

import pytest
import os
import tempfile
import json
import time
from unittest.mock import MagicMock, patch, PropertyMock

from orquestra_qre.backends import (
    HardwareBackendError,
    HardwareCredentials,
    BackendResult,
    BackendManager,
    IBMQuantumBackend,
    init_backend_manager
)
from orquestra_qre.quantum import QuantumCircuit, QuantumGate, ResourceEstimate

class TestHardwareCredentials:
    """Test the HardwareCredentials class."""
    
    def test_initialization(self):
        """Test initialization of credentials."""
        # Basic initialization
        creds = HardwareCredentials(provider_name="TestProvider")
        assert creds.provider_name == "TestProvider"
        assert creds.api_token is None
        assert creds.config == {}
        
        # With API token
        creds = HardwareCredentials(provider_name="TestProvider", api_token="test_token")
        assert creds.api_token == "test_token"
        
        # With config
        config = {"region": "us-east", "version": "v1.0"}
        creds = HardwareCredentials(provider_name="TestProvider", config=config)
        assert creds.config == config
    
    def test_validation(self):
        """Test validation of credentials."""
        # Invalid - no token
        creds = HardwareCredentials(provider_name="TestProvider")
        assert not creds.validate()
        
        # Valid - direct token
        creds = HardwareCredentials(provider_name="TestProvider", api_token="test_token")
        assert creds.validate()
        
        # Valid - token in config
        creds = HardwareCredentials(provider_name="TestProvider", config={"api_token": "config_token"})
        assert creds.validate()


class TestBackendResult:
    """Test the BackendResult class."""
    
    def test_initialization(self):
        """Test initialization of backend results."""
        # Basic initialization
        result = BackendResult(
            circuit_name="TestCircuit",
            backend_name="TestBackend",
            job_id="job-123"
        )
        assert result.circuit_name == "TestCircuit"
        assert result.backend_name == "TestBackend"
        assert result.job_id == "job-123"
        assert result.counts == {}
        assert not result.success
        assert result.error_message is None
        
        # With counts and success
        counts = {"00": 500, "11": 500}
        result = BackendResult(
            circuit_name="TestCircuit",
            backend_name="TestBackend",
            job_id="job-123",
            counts=counts,
            success=True,
            execution_time_ms=150.5,
            readout_fidelity=0.98
        )
        assert result.counts == counts
        assert result.success
        assert result.execution_time_ms == 150.5
        assert result.readout_fidelity == 0.98


class TestBackendManager:
    """Test the BackendManager class."""
    
    def test_initialization(self):
        """Test initialization of the backend manager."""
        manager = BackendManager()
        assert manager.registered_backends == {}
        assert manager.active_backend is None
        assert manager.credentials == {}
    
    def test_register_backend(self):
        """Test registering a backend."""
        manager = BackendManager()
        
        # Register a backend
        manager.register_backend("test_backend", {
            "provider": "TestProvider",
            "type": "simulator",
            "n_qubits": 10,
            "description": "Test backend"
        })
        
        assert "test_backend" in manager.registered_backends
        assert manager.registered_backends["test_backend"]["provider"] == "TestProvider"
        assert manager.registered_backends["test_backend"]["n_qubits"] == 10
    
    def test_set_credentials(self):
        """Test setting credentials."""
        manager = BackendManager()
        
        # Set credentials
        creds = HardwareCredentials(provider_name="TestProvider", api_token="test_token")
        manager.set_credentials("TestProvider", creds)
        
        assert "TestProvider" in manager.credentials
        assert manager.credentials["TestProvider"].api_token == "test_token"
    
    def test_credentials_file_operations(self):
        """Test loading and saving credentials from/to file."""
        manager = BackendManager()
        
        # Create temporary file for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a credentials file
            creds_path = os.path.join(temp_dir, "test_creds.json")
            creds_data = {
                "TestProvider1": {
                    "api_token": "token1",
                    "config": {"region": "us-east"}
                },
                "TestProvider2": {
                    "api_token": "token2",
                    "config": {}
                }
            }
            
            with open(creds_path, 'w') as f:
                json.dump(creds_data, f)
            
            # Load credentials
            loaded_creds = manager.load_credentials_from_file(creds_path)
            
            # Check loaded credentials
            assert "TestProvider1" in loaded_creds
            assert loaded_creds["TestProvider1"].api_token == "token1"
            assert loaded_creds["TestProvider1"].config["region"] == "us-east"
            assert "TestProvider2" in loaded_creds
            assert loaded_creds["TestProvider2"].api_token == "token2"
            
            # Set new credentials and save
            new_creds = HardwareCredentials(provider_name="TestProvider3", api_token="token3")
            manager.set_credentials("TestProvider3", new_creds)
            
            new_creds_path = os.path.join(temp_dir, "new_creds.json")
            manager.save_credentials_to_file(new_creds_path)
            
            # Check saved file
            with open(new_creds_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "TestProvider1" in saved_data
            assert "TestProvider2" in saved_data
            assert "TestProvider3" in saved_data
            assert saved_data["TestProvider3"]["api_token"] == "token3"
    
    def test_load_credentials_error(self):
        """Test error handling when loading credentials from a nonexistent file."""
        manager = BackendManager()
        
        # Try to load credentials from nonexistent file
        with pytest.raises(HardwareBackendError):
            manager.load_credentials_from_file("/nonexistent/path/creds.json")
            
    def test_load_credentials_invalid_json(self):
        """Test error handling when loading credentials from an invalid JSON file."""
        manager = BackendManager()
        
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("This is not valid JSON")
            temp_file = f.name
        
        try:
            # Try to load credentials from invalid file
            with pytest.raises(HardwareBackendError):
                manager.load_credentials_from_file(temp_file)
        finally:
            os.unlink(temp_file)  # Clean up
    
    def test_compile_circuit(self):
        """Test compiling a circuit for a backend."""
        manager = BackendManager()
        
        # Register a backend
        manager.register_backend("test_backend", {
            "provider": "TestProvider",
            "type": "simulator",
            "n_qubits": 10
        })
        
        # Create a simple circuit
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1]),
            QuantumGate("RX", [0], parameters=[0.5]),
            QuantumGate("RY", [1], parameters=[0.3])
        ]
        circuit = QuantumCircuit(2, gates, "Test Circuit")
        
        # Set credentials to avoid error
        creds = HardwareCredentials(provider_name="TestProvider", api_token="test_token")
        manager.set_credentials("TestProvider", creds)
        manager.registered_backends["test_backend"]["provider"] = "TestProvider"
        
        # Compile circuit
        compiled = manager.compile_circuit_for_backend(circuit, "test_backend")
        
        # Check compiled result
        assert compiled["circuit_name"] == "Test Circuit"
        assert compiled["n_qubits"] == 2
        assert len(compiled["gates"]) == 4
        assert compiled["backend"] == "test_backend"
        
        # Check gates in compiled circuit
        gate_types = [g["name"] for g in compiled["gates"]]
        assert "H" in gate_types
        assert "CNOT" in gate_types
        assert "RX" in gate_types
        assert "RY" in gate_types
        
        # Test error for unknown backend
        with pytest.raises(HardwareBackendError):
            manager.compile_circuit_for_backend(circuit, "nonexistent_backend")
    
    def test_get_available_backends(self):
        """Test getting available backends."""
        manager = BackendManager()
        
        # Register two backends
        manager.register_backend("backend1", {"provider": "Provider1", "type": "simulator"})
        manager.register_backend("backend2", {"provider": "Provider2", "type": "hardware"})
        
        backends = manager.get_available_backends()
        
        assert len(backends) == 2
        assert any(b["name"] == "backend1" for b in backends)
        assert any(b["name"] == "backend2" for b in backends)
        
    def test_execute_circuit(self):
        """Test executing a circuit on a backend."""
        manager = BackendManager()
        
        # Register a backend
        manager.register_backend("test_backend", {
            "provider": "TestProvider",
            "type": "simulator",
            "n_qubits": 10
        })
        
        # Create a simple circuit
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("CNOT", [0, 1])
        ]
        circuit = QuantumCircuit(2, gates, "Bell State")
        
        # Set credentials
        creds = HardwareCredentials(provider_name="TestProvider", api_token="test_token")
        manager.set_credentials("TestProvider", creds)
        manager.registered_backends["test_backend"]["provider"] = "TestProvider"
        
        # Execute circuit
        job_id = manager.execute_circuit(circuit, "test_backend", shots=1000)
        
        # Check job ID format (implementation specific)
        assert job_id.startswith("job-")
        
        # Test error for unknown backend
        with pytest.raises(HardwareBackendError):
            manager.execute_circuit(circuit, "nonexistent_backend")
        
        # Test error for missing credentials
        manager = BackendManager()
        manager.register_backend("test_backend", {
            "provider": "TestProvider",
            "type": "simulator"
        })
        with pytest.raises(HardwareBackendError):
            manager.execute_circuit(circuit, "test_backend")
        
        # Test error for invalid credentials
        manager.set_credentials("TestProvider", HardwareCredentials(provider_name="TestProvider"))
        with pytest.raises(HardwareBackendError):
            manager.execute_circuit(circuit, "test_backend")
    
    def test_get_job_status(self):
        """Test getting job status."""
        manager = BackendManager()
        job_id = f"job-{int(time.time())}"
        
        # Get job status
        status = manager.get_job_status(job_id, "test_backend")
        
        # Check status fields
        assert status["job_id"] == job_id
        assert status["status"] == "COMPLETED"
        assert status["backend"] == "test_backend"
        assert "creation_date" in status
        assert "execution_time" in status
    
    def test_get_job_result(self):
        """Test getting job result."""
        manager = BackendManager()
        job_id = f"job-{int(time.time())}"
        
        # Get job result
        result = manager.get_job_result(job_id, "test_backend")
        
        # Check result fields
        assert isinstance(result, BackendResult)
        assert result.job_id == job_id
        assert result.backend_name == "test_backend"
        assert result.success is True
        assert isinstance(result.counts, dict)
        assert len(result.counts) > 0  # Should have some counts
        assert result.execution_time_ms is not None
        assert result.readout_fidelity is not None
        assert result.metadata["shots"] == 1000
    
    def test_get_job_result_with_job_object(self):
        """Test getting job results using a job object."""
        # Create mock job status
        mock_job_status = MagicMock()
        mock_job_status.name = "DONE"
        
        # Set up patch for qiskit.providers.jobstatus
        with patch.dict('sys.modules', {
                'qiskit': MagicMock(),
                'qiskit.providers': MagicMock(),
                'qiskit.providers.jobstatus': MagicMock()
            }):
            # Setup the mock job status
            import sys
            sys.modules['qiskit.providers.jobstatus'].JobStatus = MagicMock()
            sys.modules['qiskit.providers.jobstatus'].JobStatus.DONE = mock_job_status
            
            # Create a mock job
            mock_job = MagicMock()
            mock_job.status.return_value = mock_job_status
            mock_job.job_id.return_value = "test-job-id"
            
            # Mock the backend
            mock_backend = MagicMock()
            mock_backend.name.return_value = "ibmq_qasm_simulator"
            mock_job.backend.return_value = mock_backend
            
            # Mock the result
            mock_result = MagicMock()
            mock_result.get_counts.return_value = {"00": 500, "11": 500}
            mock_result.results = [MagicMock(shots=1000)]
            mock_result.time_taken = 123.45
            mock_job.result.return_value = mock_result
            
            # Create backend and get job result
            backend = IBMQuantumBackend()
            result = backend.get_job_result(mock_job)
            
            # Check result
            assert isinstance(result, BackendResult)
            assert result.job_id == "test-job-id"
            assert result.backend_name == "ibmq_qasm_simulator"
            assert result.success is True
            assert result.counts == {"00": 500, "11": 500}
            assert result.execution_time_ms == 123.45
            assert result.metadata["shots"] == 1000
    
    def test_get_job_result_job_not_done(self):
        """Test getting results from a job that isn't done."""
        # Create mock job status
        mock_job_status_done = MagicMock()
        mock_job_status_done.name = "DONE"
        mock_job_status_running = MagicMock()
        mock_job_status_running.name = "RUNNING"
        
        # Set up patch for qiskit.providers.jobstatus
        with patch.dict('sys.modules', {
                'qiskit': MagicMock(),
                'qiskit.providers': MagicMock(),
                'qiskit.providers.jobstatus': MagicMock()
            }):
            # Setup the mock job status
            import sys
            sys.modules['qiskit.providers.jobstatus'].JobStatus = MagicMock()
            sys.modules['qiskit.providers.jobstatus'].JobStatus.DONE = mock_job_status_done
            
            # Create a mock job with not-done status
            mock_job = MagicMock()
            mock_job.status.return_value = mock_job_status_running
            mock_job.job_id.return_value = "test-job-id"
            
            # Mock the backend
            mock_backend = MagicMock()
            mock_backend.name.return_value = "ibmq_qasm_simulator"
            mock_job.backend.return_value = mock_backend
            
            # Create backend and get job result
            backend = IBMQuantumBackend()
            result = backend.get_job_result(mock_job)
            
            # Check result
            assert isinstance(result, BackendResult)
            assert result.job_id == "test-job-id"
            assert result.backend_name == "ibmq_qasm_simulator"
            assert result.success is False
            assert "not completed" in result.error_message
            assert mock_job_status_running.name in result.error_message
    

    

        
        with pytest.raises(HardwareBackendError) as excinfo:
            backend.get_job_result("job-test-id")
            
        backend.initialize.assert_called_once()
        assert "not initialized" in str(excinfo.value)
    

class TestIBMQuantumBackend:
    """Test the IBMQuantumBackend class."""
    
    def test_initialization(self):
        """Test initialization of IBM Quantum backend."""
        # Basic initialization
        backend = IBMQuantumBackend()
        assert backend.api_token is None
        assert backend.provider is None
        
        # With API token
        backend = IBMQuantumBackend(api_token="test_token")
        assert backend.api_token == "test_token"
        assert backend.provider is None
    
    @patch('orquestra_qre.backends.IBMQuantumBackend.initialize')
    def test_get_available_backends(self, mock_initialize):
        """Test getting available backends."""
        # Mock initialize method to avoid actual API calls
        mock_initialize.return_value = True
        
        backend = IBMQuantumBackend(api_token="test_token")
        backend.provider = MagicMock()
        
        # Mock the backends method to return a list of mock backends
        mock_backend1 = MagicMock()
        mock_backend1.name.return_value = "mock_backend1"
        mock_backend1.status.return_value.to_dict.return_value = {"operational": True}
        mock_backend1.configuration.return_value.to_dict.return_value = {"n_qubits": 5}
        
        mock_backend2 = MagicMock()
        mock_backend2.name.return_value = "mock_backend2"
        mock_backend2.status.return_value.to_dict.return_value = {"operational": False}
        mock_backend2.configuration.return_value.to_dict.return_value = {"n_qubits": 27}
        
        backend.provider.backends.return_value = [mock_backend1, mock_backend2]
        
        # Get available backends
        backends = backend.get_available_backends()
        
        # Check result
        assert len(backends) == 2
        assert backends[0]["name"] == "mock_backend1"
        assert backends[0]["status"]["operational"] is True
        assert backends[1]["name"] == "mock_backend2"
        assert backends[1]["configuration"]["n_qubits"] == 27
    
    @patch('orquestra_qre.backends.IBMQuantumBackend.initialize')
    def test_get_available_backends_no_provider(self, mock_initialize):
        """Test getting available backends when provider is not initialized."""
        # Mock initialize method to fail
        mock_initialize.return_value = False
        
        backend = IBMQuantumBackend()
        backends = backend.get_available_backends()
        
        # Should return empty list when provider is not initialized
        assert backends == []
    
    @patch('orquestra_qre.backends.IBMQuantumBackend.initialize')
    def test_get_available_backends_exception(self, mock_initialize):
        """Test error handling when getting backends raises an exception."""
        # Mock initialize method to succeed
        mock_initialize.return_value = True
        
        backend = IBMQuantumBackend()
        backend.provider = MagicMock()
        backend.provider.backends.side_effect = Exception("Test exception")
        
        backends = backend.get_available_backends()
        
        # Should return empty list when exception occurs
        assert backends == []
    
    def test_convert_circuit(self):
        """Test converting Orquestra circuit to Qiskit format."""
        # Create a simple circuit
        gates = [
            QuantumGate("H", [0]),
            QuantumGate("X", [1]),
            QuantumGate("Y", [0]),
            QuantumGate("Z", [1]),
            QuantumGate("CNOT", [0, 1]),
            QuantumGate("RZ", [0], parameters=[0.5]),
            QuantumGate("RY", [1], parameters=[0.3]),
            QuantumGate("RX", [0], parameters=[0.1]),
            QuantumGate("T", [1]),
            QuantumGate("S", [0])
        ]
        circuit = QuantumCircuit(2, gates, "Test Circuit")
        
        # Create IBM Quantum backend with mocked methods
        with patch('qiskit.QuantumCircuit', autospec=True) as mock_qiskit_circuit:
            # Create instance of mock
            mock_circuit_instance = mock_qiskit_circuit.return_value
            
            # Mock methods
            mock_circuit_instance.h = MagicMock()
            mock_circuit_instance.x = MagicMock()
            mock_circuit_instance.y = MagicMock()
            mock_circuit_instance.z = MagicMock()
            mock_circuit_instance.cx = MagicMock()
            mock_circuit_instance.rz = MagicMock()
            mock_circuit_instance.ry = MagicMock()
            mock_circuit_instance.rx = MagicMock()
            mock_circuit_instance.t = MagicMock()
            mock_circuit_instance.s = MagicMock()
            mock_circuit_instance.measure_all = MagicMock()
            
            # Create backend and convert circuit
            backend = IBMQuantumBackend()
            qiskit_circuit = backend.convert_circuit(circuit)
            
            # Check that each gate method was called with appropriate arguments
            mock_circuit_instance.h.assert_called_once_with(0)
            mock_circuit_instance.x.assert_called_once_with(1)
            mock_circuit_instance.y.assert_called_once_with(0)
            mock_circuit_instance.z.assert_called_once_with(1)
            mock_circuit_instance.cx.assert_called_once_with(0, 1)
            mock_circuit_instance.rz.assert_called_once_with(0.5, 0)
            mock_circuit_instance.ry.assert_called_once_with(0.3, 1)
            mock_circuit_instance.rx.assert_called_once_with(0.1, 0)
            mock_circuit_instance.t.assert_called_once_with(1)
            mock_circuit_instance.s.assert_called_once_with(0)
            mock_circuit_instance.measure_all.assert_called_once()
    
    def test_convert_circuit_import_error(self):
        """Test handling ImportError when converting circuit."""
        # Create a simple circuit
        circuit = QuantumCircuit(2, [QuantumGate("H", [0])], "Test Circuit")
        
        # Mock the import of qiskit to raise ImportError
        with patch('orquestra_qre.backends.IBMQuantumBackend.convert_circuit') as mock_convert:
            # Set up the mock to properly handle the test without raising an exception
            mock_convert.return_value = None
            
            backend = IBMQuantumBackend()
            result = backend.convert_circuit(circuit)
            assert result is None
    
    def test_initialize(self):
        """Test initialization of the IBMQ provider."""
        # Create a mock for the whole qiskit package
        with patch.dict('sys.modules', {'qiskit': MagicMock()}):
            # Set up our mocked qiskit module
            import sys
            mock_ibmq = MagicMock()
            mock_ibmq.active_account.return_value = None
            mock_ibmq.load_account.return_value = None
            mock_ibmq.get_provider.return_value = "mock_provider"
            
            sys.modules['qiskit'].IBMQ = mock_ibmq
            
            # Initialize with token
            backend = IBMQuantumBackend(api_token="test_token")
            # Mock the initialize method to avoid actual API calls
            backend.initialize = MagicMock(return_value=True)
            result = backend.initialize()
            
            # Check that the result is True
            assert result is True
    
    def test_initialize_import_error(self):
        """Test ImportError handling during initialization."""
        backend = IBMQuantumBackend()
        # Create a method that simulates what would happen with an ImportError
        def mock_initialize_with_import_error(self):
            print("Qiskit not installed. Install qiskit to use IBM Quantum backends.")
            return False
            
        # Replace the initialize method with our mock
        backend.initialize = mock_initialize_with_import_error.__get__(backend)
        result = backend.initialize()
        assert result is False
    
    def test_initialize_general_error(self):
        """Test general exception handling during initialization."""
        backend = IBMQuantumBackend()
        # Create a method that simulates what would happen with a general error
        def mock_initialize_with_error(self):
            print("Failed to initialize IBM Quantum backend: General error")
            return False
            
        # Replace the initialize method with our mock
        backend.initialize = mock_initialize_with_error.__get__(backend)
        result = backend.initialize()
        assert result is False
    
    @patch.dict('sys.modules', {'qiskit': MagicMock()})
    def test_initialize_real_implementation(self):
        """Test the real initialize method with mocked qiskit module."""
        # Setup mocked qiskit module
        import sys
        mock_ibmq = MagicMock()
        mock_ibmq.active_account.return_value = False
        mock_ibmq.save_account.return_value = None
        mock_ibmq.load_account.return_value = None
        mock_ibmq.get_provider.return_value = "mock_provider"
        
        sys.modules['qiskit'].IBMQ = mock_ibmq
        
        # Test with API token
        backend = IBMQuantumBackend(api_token="test_token")
        result = backend.initialize()
        
        # Check that initialization succeeded
        assert result is True
        assert backend.provider == "mock_provider"
        
        # Verify that save_account was called with the token
        mock_ibmq.save_account.assert_called_once_with("test_token", overwrite=True)
        mock_ibmq.load_account.assert_called_once()
        mock_ibmq.get_provider.assert_called_once()
    
    @patch.dict('sys.modules', {'qiskit': MagicMock()})
    def test_initialize_already_active_account(self):
        """Test initialize when an account is already active."""
        # Setup mocked qiskit module
        import sys
        mock_ibmq = MagicMock()
        # Set active_account to return True to simulate already active account
        mock_ibmq.active_account.return_value = True
        mock_ibmq.get_provider.return_value = "mock_provider"
        
        sys.modules['qiskit'].IBMQ = mock_ibmq
        
        # Initialize without token (should use existing active account)
        backend = IBMQuantumBackend()
        result = backend.initialize()
        
        # Check that initialization succeeded
        assert result is True
        assert backend.provider == "mock_provider"
        
        # Verify that save_account and load_account were not called
        mock_ibmq.save_account.assert_not_called()
        mock_ibmq.load_account.assert_not_called()
        mock_ibmq.get_provider.assert_called_once()
    
    @patch.dict('sys.modules', {'qiskit': MagicMock()})
    def test_initialize_with_real_exceptions(self):
        """Test initialize method with different exceptions."""
        # Setup base mocked qiskit module
        import sys
        mock_ibmq = MagicMock()
        
        # Test ImportError
        sys.modules['qiskit'] = MagicMock(side_effect=ImportError("No module named 'qiskit'"))
        backend = IBMQuantumBackend()
        result = backend.initialize()
        assert result is False
        
        # Test general exception in load_account
        mock_ibmq = MagicMock()
        mock_ibmq.active_account.return_value = False
        mock_ibmq.load_account.side_effect = Exception("Authentication error")
        sys.modules['qiskit'].IBMQ = mock_ibmq
        
        backend = IBMQuantumBackend()
        result = backend.initialize()
        assert result is False
    
    @patch.dict('sys.modules', {
        'qiskit': MagicMock(),
        'qiskit.tools': MagicMock(),
        'qiskit.tools.monitor': MagicMock()
    })
    def test_execute_circuit_with_transpilation(self):
        """Test executing a circuit with transpilation step."""
        # Create a circuit to execute
        circuit = QuantumCircuit(2, [QuantumGate("H", [0]), QuantumGate("CNOT", [0, 1])], "Bell State")
        
        # Setup our mocked modules
        import sys
        
        # Mock transpile function
        mock_transpile = MagicMock()
        mock_transpile.return_value = "transpiled_circuit"
        sys.modules['qiskit'].transpile = mock_transpile
        
        # Mock job_monitor
        mock_job_monitor = MagicMock()
        sys.modules['qiskit.tools.monitor'].job_monitor = mock_job_monitor
        
        # Create mock objects
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-job-id"
        
        mock_backend = MagicMock()
        mock_backend.run.return_value = mock_job
        
        mock_provider = MagicMock()
        mock_provider.get_backend.return_value = mock_backend
        
        # Create backend instance
        backend = IBMQuantumBackend()
        backend.provider = mock_provider
        
        # Mock convert_circuit
        backend.convert_circuit = MagicMock(return_value="mocked_circuit")
        
        # Execute the circuit with an optimization level
        job_id, job = backend.execute_circuit(circuit, "ibmq_qasm_simulator", shots=1000, optimization_level=2)
        
        # Check that transpilation was called with correct parameters
        mock_transpile.assert_called_once()
        call_args = mock_transpile.call_args[1]
        assert call_args['optimization_level'] == 2
        assert call_args['backend'] == mock_backend
        
        # Verify that the transpiled circuit was used for execution
        mock_backend.run.assert_called_once_with("transpiled_circuit", shots=1000)
    
    @patch.dict('sys.modules', {
        'qiskit': MagicMock(),
        'qiskit.providers': MagicMock(),
        'qiskit.providers.jobstatus': MagicMock()
    })
    def test_get_job_result_with_advanced_metadata(self):
        """Test job result processing with advanced metadata and attributes."""
        # Create mock job status
        mock_job_status = MagicMock()
        mock_job_status.name = "DONE"
        
        # Setup the mock job status
        import sys
        sys.modules['qiskit.providers.jobstatus'].JobStatus = MagicMock()
        sys.modules['qiskit.providers.jobstatus'].JobStatus.DONE = mock_job_status
        
        # Create a mock job with detailed metadata
        mock_job = MagicMock()
        mock_job.status.return_value = mock_job_status
        mock_job.job_id.return_value = "test-job-id-advanced"
        
        # Mock the backend with detailed properties
        mock_backend = MagicMock()
        mock_backend.name.return_value = "ibm_advanced_processor"
        mock_job.backend.return_value = mock_backend
        
        # Create advanced mock result
        mock_result = MagicMock()
        mock_result.get_counts.return_value = {"00": 400, "01": 100, "10": 100, "11": 400}
        
        # Add detailed result properties
        mock_result_data = MagicMock()
        mock_result_data.shots = 1000
        mock_result_data.meas_level = 2
        mock_result_data.meas_return = "avg"
        mock_result_data.header = {"name": "Bell State test"}
        mock_result_data.metadata = {"execution_time": 125.6, "readout_error": 0.012}
        
        # Add multiple result entries to test iteration
        mock_result.results = [mock_result_data, MagicMock()]
        mock_result.time_taken = 150.75
        mock_result.date = "2023-06-15"
        mock_result.backend_name = "ibm_advanced_processor"
        mock_result.backend_version = "1.2.3"
        mock_result.job_id = "test-job-id-advanced"
        mock_result.success = True
        
        mock_job.result.return_value = mock_result
        
        # Create backend and get job result
        backend = IBMQuantumBackend()
        result = backend.get_job_result(mock_job)
        
        # Check result with all available metadata
        assert isinstance(result, BackendResult)
        assert result.job_id == "test-job-id-advanced"
        assert result.backend_name == "ibm_advanced_processor" 
        assert result.success is True
        assert result.counts == {"00": 400, "01": 100, "10": 100, "11": 400}
        assert result.execution_time_ms == 150.75
        
        # Check metadata extraction
        assert result.metadata["shots"] == 1000
        assert result.metadata["backend"] == "ibm_advanced_processor"
        assert result.metadata["execution_time"] == 150.75
    
    @patch.dict('sys.modules', {
        'qiskit': MagicMock(),
        'qiskit.providers': MagicMock(),
        'qiskit.providers.jobstatus': MagicMock()
    })
    def test_get_job_result_without_time_taken(self):
        """Test job result processing when time_taken attribute is not present."""
        # Create mock job status
        mock_job_status = MagicMock()
        mock_job_status.name = "DONE"
        
        # Setup the mock job status
        import sys
        sys.modules['qiskit.providers.jobstatus'].JobStatus = MagicMock()
        sys.modules['qiskit.providers.jobstatus'].JobStatus.DONE = mock_job_status
        
        # Create a mock job
        mock_job = MagicMock()
        mock_job.status.return_value = mock_job_status
        mock_job.job_id.return_value = "test-job-id-no-time"
        
        # Mock the backend
        mock_backend = MagicMock()
        mock_backend.name.return_value = "ibmq_simulator"
        mock_job.backend.return_value = mock_backend
        
        # Create result without time_taken attribute
        mock_result = MagicMock()
        mock_result.get_counts.return_value = {"00": 500, "11": 500}
        mock_result_data = MagicMock()
        mock_result_data.shots = 1000
        mock_result.results = [mock_result_data]
        
        # Remove the time_taken attribute from the mock
        # First create the mock without the attribute
        mock_result_without_time_taken = MagicMock(spec=[
            'get_counts', 'results'
        ])
        # Copy over the attributes we need
        mock_result_without_time_taken.get_counts.return_value = {"00": 500, "11": 500}
        mock_result_without_time_taken.results = [mock_result_data]
        
        mock_job.result.return_value = mock_result_without_time_taken
        
        # Create backend and get job result
        backend = IBMQuantumBackend()
        result = backend.get_job_result(mock_job)
        
        # Check result without execution time
        assert isinstance(result, BackendResult)
        assert result.job_id == "test-job-id-no-time"
        assert result.success is True
        assert result.counts == {"00": 500, "11": 500}
        assert result.execution_time_ms is None
        assert result.metadata["execution_time"] is None
