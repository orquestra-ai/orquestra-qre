"""Streamlit version of Orquestra QRE - Much simpler!"""

# --- Move set_page_config to the very top of the file ---
import streamlit as st
st.set_page_config(
    page_title="⚛️ Orquestra QRE",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Ensure session state is initialized at the very top, before any access ---
if 'estimations_history' not in st.session_state:
    st.session_state.estimations_history = []
if 'circuit_library' not in st.session_state:
    st.session_state.circuit_library = []
if 'custom_gates' not in st.session_state:
    st.session_state.custom_gates = []
if 'custom_num_qubits' not in st.session_state:
    st.session_state.custom_num_qubits = 2
if 'jobs_history' not in st.session_state:
    st.session_state.jobs_history = []
if 'api_tokens' not in st.session_state:
    st.session_state.api_tokens = {
        'IBM': '',
        'IonQ': '',
        'Rigetti': ''
    }
if 'show_connectivity_analysis' not in st.session_state:
    st.session_state.show_connectivity_analysis = False

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from dataclasses import dataclass

# --- Hardware Provider and Error Correction Models ---
@dataclass
class HardwareProvider:
    name: str
    max_qubits: int
    coherence_time_us: float
    single_qubit_error: float
    two_qubit_error: float
    connectivity: str
    real_hardware_available: bool = False
    
    def to_dict(self):
        return {
            'name': self.name,
            'max_qubits': self.max_qubits,
            'coherence_time_us': self.coherence_time_us,
            'single_qubit_error': self.single_qubit_error,
            'two_qubit_error': self.two_qubit_error,
            'connectivity': self.connectivity,
            'real_hardware_available': self.real_hardware_available
        }

# Example providers (extend as needed)
HARDWARE_PROVIDERS = [
    HardwareProvider("IBM", 127, 100, 1e-3, 1e-2, "Heavy Hex", True),
    HardwareProvider("Google", 72, 150, 5e-4, 1e-2, "Sycamore", True),
    HardwareProvider("IonQ", 32, 1000, 1e-4, 2e-3, "All-to-All", True),
    HardwareProvider("Rigetti", 80, 80, 2e-3, 1.5e-2, "Lattice", True),
    HardwareProvider("Custom", 1000, 10000, 1e-5, 1e-4, "Custom", False)
]

ERROR_CORRECTION_CODES = {
    "None": {"overhead": 1, "logical_to_physical": lambda n: n},
    "Surface Code": {"overhead": 20, "logical_to_physical": lambda n: n * 20},
    "Repetition Code": {"overhead": 5, "logical_to_physical": lambda n: n * 5}
}

# --- Estimator Initialization ---
@st.cache_resource
def get_components():
    from orquestra_qre.quantum import CircuitGenerator, QuantumResourceEstimator
    from orquestra_qre.connectivity import CONNECTIVITY_MODELS, SWAPEstimator
    from orquestra_qre.backends import init_backend_manager
    
    backend_manager = init_backend_manager()
    return CircuitGenerator(), QuantumResourceEstimator(), CONNECTIVITY_MODELS, SWAPEstimator(), backend_manager

circuit_gen, estimator, CONNECTIVITY_MODELS, swap_estimator, backend_manager = get_components()

# --- Helper: Hardware-aware estimation wrapper ---
def hardware_aware_estimate(circuit, estimator, provider, ec_code, connectivity_model=None, swap_estimator=None):
    logical_qubits = circuit.num_qubits
    physical_qubits = ec_code["logical_to_physical"](logical_qubits)
    estimate = estimator.estimate_resources(circuit)
    
    # Add connectivity and SWAP analysis if provided
    swap_overhead_data = None
    if connectivity_model and swap_estimator:
        try:
            # Create connectivity graph for the provider
            connectivity_graph = connectivity_model(circuit.num_qubits)
            
            # Analyze SWAP overhead
            swap_overhead_data = swap_estimator.estimate_swap_overhead(circuit, connectivity_graph)
            
            # Adjust gate count and depth based on SWAP overhead
            if 'error' not in swap_overhead_data:
                estimate.gate_count = swap_overhead_data['routed_gate_count']
                estimate.depth += swap_overhead_data['swap_depth_overhead']
                
                # Adjust runtime and fidelity based on additional gates
                routing_factor = swap_overhead_data['routing_factor']
                estimate.estimated_runtime_ms *= routing_factor
                # Each additional CNOT decreases fidelity by two-qubit error rate
                additional_cnots = swap_overhead_data.get('additional_cnots_from_swaps', 0)
                if additional_cnots > 0:
                    estimate.estimated_fidelity *= (1 - provider.two_qubit_error) ** additional_cnots
        except Exception as e:
            swap_overhead_data = {"error": str(e)}
    
    # Adjust runtime and fidelity for error correction (simple model)
    overhead = ec_code["overhead"]
    estimate.estimated_runtime_ms *= overhead
    estimate.estimated_fidelity **= overhead
    
    # Hardware feasibility checks
    warnings = []
    if physical_qubits > provider.max_qubits:
        warnings.append(f"⚠️ Circuit requires {physical_qubits} physical qubits, but {provider.name} supports only {provider.max_qubits}.")
    if estimate.estimated_runtime_ms > provider.coherence_time_us / 1000:
        warnings.append(f"⚠️ Estimated runtime {estimate.estimated_runtime_ms:.1f} ms exceeds {provider.coherence_time_us} μs coherence time.")
    
    # Add SWAP-related warnings
    if swap_overhead_data and 'error' in swap_overhead_data:
        warnings.append(f"⚠️ SWAP analysis error: {swap_overhead_data['error']}")
    elif swap_overhead_data and swap_overhead_data['approx_swap_count'] > 0:
        warnings.append(f"ℹ️ {swap_overhead_data['approx_swap_count']} SWAP gates required for {provider.connectivity} connectivity.")
        
    estimate.hardware_warnings = warnings
    estimate.physical_qubits = physical_qubits
    estimate.selected_provider = provider.name
    estimate.selected_ec_code = ec_code
    estimate.swap_overhead = swap_overhead_data
    
    return estimate

# --- Create Circuit Visual ---
def create_circuit_visual(circuit):
    """Create a visual representation of the quantum circuit."""
    lines = []
    num_qubits = circuit.num_qubits
    
    # Header
    lines.append("Quantum Circuit Diagram:")
    lines.append("=" * 50)
    
    # Initialize qubit lines
    qubit_lines = []
    for i in range(num_qubits):
        qubit_lines.append(f"q{i}: |0⟩ ")
    
    # Add gates
    max_line_length = max(len(line) for line in qubit_lines)
    
    for gate in circuit.gates:
        # Pad all lines to same length
        for i in range(num_qubits):
            while len(qubit_lines[i]) < max_line_length:
                qubit_lines[i] += "─"
        
        # Add gate symbols
        if gate.name == "H":
            qubit_lines[gate.qubits[0]] += "─[H]─"
        elif gate.name == "X":
            qubit_lines[gate.qubits[0]] += "─[X]─"
        elif gate.name == "Y":
            qubit_lines[gate.qubits[0]] += "─[Y]─"
        elif gate.name == "Z":
            qubit_lines[gate.qubits[0]] += "─[Z]─"
        elif gate.name == "T":
            qubit_lines[gate.qubits[0]] += "─[T]─"
        elif gate.name == "S":
            qubit_lines[gate.qubits[0]] += "─[S]─"
        elif gate.name in ["RZ", "RY"]:
            angle = gate.parameters[0] if gate.parameters else 0
            qubit_lines[gate.qubits[0]] += f"─[R{gate.name[1]}({angle:.2f})]─"
        elif gate.name == "CNOT":
            control, target = gate.qubits[0], gate.qubits[1]
            qubit_lines[control] += "─●─"
            qubit_lines[target] += "─⊕─"
        
        # Pad other qubits
        max_line_length = max(len(line) for line in qubit_lines)
        for i in range(num_qubits):
            if i not in gate.qubits:
                while len(qubit_lines[i]) < max_line_length:
                    qubit_lines[i] += "─"
    
    # Add final padding
    for i in range(num_qubits):
        qubit_lines[i] += "─"
    
    lines.extend(qubit_lines)
    return "\n".join(lines)

def create_interactive_circuit_plot(circuit):
    """Create an interactive Plotly visualization of the circuit."""
    fig = go.Figure()
    
    num_qubits = circuit.num_qubits
    num_gates = len(circuit.gates)
    
    # Draw qubit lines
    for q in range(num_qubits):
        fig.add_trace(go.Scatter(
            x=[0, num_gates + 1],
            y=[q, q],
            mode='lines',
            line=dict(color='black', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Qubit labels
        fig.add_annotation(
            x=-0.5, y=q,
            text=f"q{q}",
            showarrow=False,
            font=dict(size=14)
        )
    
    # Draw gates
    gate_colors = {
        'H': '#FF6B6B', 'X': '#4ECDC4', 'Y': '#45B7D1', 'Z': '#96CEB4',
        'T': '#FFEAA7', 'S': '#DDA0DD', 'RZ': '#F39C12', 'RY': '#E74C3C',
        'CNOT': '#9B59B6'
    }
    
    for i, gate in enumerate(circuit.gates):
        gate_x = i + 1
        color = gate_colors.get(gate.name, '#95A5A6')
        
        if gate.name == "CNOT":
            control, target = gate.qubits[0], gate.qubits[1]
            
            # Control dot
            fig.add_trace(go.Scatter(
                x=[gate_x], y=[control],
                mode='markers',
                marker=dict(size=15, color='black', symbol='circle'),
                showlegend=False,
                hovertemplate=f"CNOT Control<br>Step: {i+1}<extra></extra>"
            ))
            
            # Target symbol
            fig.add_trace(go.Scatter(
                x=[gate_x], y=[target],
                mode='markers',
                marker=dict(size=20, color='white', symbol='circle', line=dict(color='black', width=2)),
                showlegend=False,
                hovertemplate=f"CNOT Target<br>Step: {i+1}<extra></extra>"
            ))
            
            # Connection line
            fig.add_trace(go.Scatter(
                x=[gate_x, gate_x],
                y=[control, target],
                mode='lines',
                line=dict(color='black', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
        else:
            # Single qubit gate
            qubit = gate.qubits[0]
            gate_text = gate.name
            if gate.parameters:
                gate_text += f"({gate.parameters[0]:.2f})"
            
            fig.add_trace(go.Scatter(
                x=[gate_x], y=[qubit],
                mode='markers+text',
                marker=dict(size=30, color=color, symbol='square'),
                text=[gate_text],
                textposition='middle center',
                textfont=dict(color='white', size=10),
                showlegend=False,
                hovertemplate=f"{gate.name} Gate<br>Qubit: {qubit}<br>Step: {i+1}<extra></extra>"
            ))
    
    fig.update_layout(
        title="Interactive Quantum Circuit",
        xaxis=dict(title="Gate Sequence", showgrid=False, zeroline=False),
        yaxis=dict(title="Qubits", showgrid=False, zeroline=False, autorange="reversed"),
        height=max(300, num_qubits * 60),
        plot_bgcolor='white',
        hovermode='closest'
    )
    
    return fig

# --- Update comparison chart to show provider and error correction ---
def create_resource_comparison_chart(estimations_history):
    """Create interactive comparison charts for multiple circuits."""
    if not estimations_history:
        return None
    
    df = pd.DataFrame([{
        'Circuit': est['circuit_name'],
        'Runtime (ms)': est['estimated_runtime_ms'],
        'Fidelity (%)': est['estimated_fidelity'] * 100,
        'Gate Count': est['gate_count'],
        'Depth': est['depth'],
        'Qubits': est['num_qubits'],
        'Physical Qubits': est.get('physical_qubits', est['num_qubits']),
        'Provider': est.get('provider', 'N/A'),
        'Error Correction': est.get('error_correction', 'None')
    } for est in estimations_history])
    
    fig = go.Figure()
    
    # Runtime vs Fidelity scatter, color by provider, size by physical qubits
    fig.add_trace(go.Scatter(
        x=df['Runtime (ms)'],
        y=df['Fidelity (%)'],
        mode='markers+text',
        marker=dict(
            size=df['Physical Qubits'],
            color=df['Provider'].astype('category').cat.codes,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Provider (code)")
        ),
        text=df['Circuit'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>' +
                      'Provider: %{marker.color}<br>' +
                      'Runtime: %{x:.1f} ms<br>' +
                      'Fidelity: %{y:.1f}%<br>' +
                      'Physical Qubits: %{marker.size}<br>' +
                      'Error Correction: %{customdata[0]}<extra></extra>',
        customdata=np.stack([df['Error Correction']], axis=-1)
    ))
    
    fig.update_layout(
        title="Circuit Performance Comparison",
        xaxis_title="Runtime (ms)",
        yaxis_title="Fidelity (%)",
        height=500
    )
    
    return fig

# --- Sidebar: Hardware Provider, Connectivity & Error Correction ---
st.sidebar.header("🖥️ Hardware Provider & Error Correction")

provider_names = [p.name for p in HARDWARE_PROVIDERS]
selected_provider_name = st.sidebar.selectbox("Select Hardware Provider", provider_names)
selected_provider = next(p for p in HARDWARE_PROVIDERS if p.name == selected_provider_name)

# Connectivity analysis section
connectivity_toggle = st.sidebar.checkbox("Enable Connectivity Analysis", value=st.session_state.show_connectivity_analysis)
st.session_state.show_connectivity_analysis = connectivity_toggle

if connectivity_toggle:
    connectivity_options = list(CONNECTIVITY_MODELS.keys())
    if selected_provider_name not in connectivity_options:
        connectivity_type = st.sidebar.selectbox("Connectivity Model", connectivity_options)
    else:
        # Default to provider's connectivity model
        connectivity_type = selected_provider_name
    
    selected_connectivity_model = CONNECTIVITY_MODELS[connectivity_type]
else:
    selected_connectivity_model = None

# Error correction section
error_correction_enabled = st.sidebar.checkbox("Enable Error Correction", value=False)
if error_correction_enabled:
    selected_ec_code = st.sidebar.selectbox("Error Correction Code", list(ERROR_CORRECTION_CODES.keys())[1:])
else:
    selected_ec_code = "None"

selected_ec = ERROR_CORRECTION_CODES[selected_ec_code]

# Real hardware backend section (only show if provider has real hardware)
if selected_provider.real_hardware_available:
    st.sidebar.header("🔬 Real Hardware Execution")
    show_backends = st.sidebar.checkbox("Connect to Real Hardware", value=False)
    
    if show_backends:
        # Backend selection
        available_backends = [b for b in backend_manager.get_available_backends() 
                            if b.get('provider', '') == selected_provider_name]
        
        if available_backends:
            backend_names = [b['name'] for b in available_backends]
            selected_backend = st.sidebar.selectbox("Select Backend", backend_names)
            
            # API token input
            api_token = st.sidebar.text_input(
                f"{selected_provider_name} API Token", 
                value=st.session_state.api_tokens.get(selected_provider_name, ""),
                type="password"
            )
            st.session_state.api_tokens[selected_provider_name] = api_token
            
            # Save credentials button
            if st.sidebar.button("💾 Save Credentials"):
                from orquestra_qre.backends import HardwareCredentials
                if api_token:
                    backend_manager.set_credentials(
                        selected_provider_name,
                        HardwareCredentials(provider_name=selected_provider_name, api_token=api_token)
                    )
                    st.sidebar.success(f"Saved {selected_provider_name} credentials!")
                else:
                    st.sidebar.error("API token cannot be empty")
        else:
            st.sidebar.info(f"No backends available for {selected_provider_name}")
            selected_backend = None
    else:
        selected_backend = None
else:
    selected_backend = None

# --- Sidebar: Circuit Selection and Builder ---
st.sidebar.header("🔬 Circuit Options")

option_mode = st.sidebar.radio(
    "Choose Mode",
    ["🎯 Pre-built Circuits", "🔧 Build Custom Circuit"]
)

MAX_QUBITS = 1000

if option_mode == "🎯 Pre-built Circuits":
    circuit_type = st.sidebar.selectbox(
        "Choose Circuit Type",
        ["Bell State", "Grover Search", "QFT", "Random Circuit", "VQE Circuit", "QAOA Circuit"]
    )
    if circuit_type == "Grover Search":
        n_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, 3)
    elif circuit_type == "QFT":
        n_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, 3)
    elif circuit_type == "Random Circuit":
        n_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, 4)
        n_gates = st.sidebar.slider("Number of Gates", 5, 200, 10)
    elif circuit_type == "VQE Circuit":
        n_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, 4)
        layers = st.sidebar.slider("Number of Variational Layers", 1, 10, 2)
        ansatz_type = st.sidebar.selectbox(
            "VQE Ansatz Type",
            ["Hardware-Efficient", "UCCSD", "Custom"]
        )
        if ansatz_type == "Custom":
            entanglement = st.sidebar.selectbox(
                "Entanglement Pattern",
                ["Linear", "Full", "Circular"]
            )
        else:
            entanglement = "Linear"
    elif circuit_type == "QAOA Circuit":
        n_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, 4)
        p_steps = st.sidebar.slider("Number of QAOA Steps", 1, 5, 1)
        problem_type = st.sidebar.selectbox(
            "Problem Type",
            ["MaxCut", "Number Partitioning", "Random"]
        )

    if st.sidebar.button("🎯 Generate Circuit"):
        # Generate circuit based on selection
        if circuit_type == "Bell State":
            circuit = circuit_gen.generate_bell_state()
        elif circuit_type == "Grover Search":
            circuit = circuit_gen.generate_grover_search(n_qubits)
        elif circuit_type == "QFT":
            circuit = circuit_gen.generate_qft(n_qubits)
        elif circuit_type == "VQE Circuit":
            # Pass the entanglement pattern for custom VQE
            if ansatz_type == "Custom":
                circuit = circuit_gen.generate_vqe_circuit(n_qubits, layers, entanglement_pattern=entanglement.lower())
            elif ansatz_type == "UCCSD":
                circuit = circuit_gen.generate_vqe_circuit(n_qubits, layers, ansatz_type="uccsd")
            else:
                circuit = circuit_gen.generate_vqe_circuit(n_qubits, layers)
            # Set a more descriptive name
            circuit.name = f"VQE {ansatz_type} ({n_qubits} qubits, {layers} layers)"
        elif circuit_type == "QAOA Circuit":
            circuit = circuit_gen.generate_qaoa_circuit(n_qubits, p_steps, problem_type=problem_type.lower())
            # Set a more descriptive name
            circuit.name = f"QAOA {problem_type} ({n_qubits} qubits, p={p_steps})"
        else:  # Random Circuit
            circuit = circuit_gen.generate_random_circuit(n_qubits, n_gates)
        
        # Store in session state
        st.session_state.current_circuit = circuit
else:
    # Custom circuit builder section
    st.sidebar.subheader("🔧 Circuit Builder")
    
    # Circuit parameters
    custom_num_qubits = st.sidebar.slider("Number of Qubits", 2, MAX_QUBITS, st.session_state.custom_num_qubits)
    st.session_state.custom_num_qubits = custom_num_qubits
    
    # Gate selection
    gate_type = st.sidebar.selectbox(
        "Add Gate",
        ["H", "X", "Y", "Z", "T", "S", "RZ", "RY", "CNOT"]
    )
    
    # Qubit selection based on gate type
    if gate_type == "CNOT":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            control_qubit = st.selectbox("Control", range(custom_num_qubits))
        with col2:
            target_qubit = st.selectbox("Target", [q for q in range(custom_num_qubits) if q != control_qubit])
        qubits = [control_qubit, target_qubit]
    else:
        target_qubit = st.sidebar.selectbox("Target Qubit", range(custom_num_qubits))
        qubits = [target_qubit]
    
    # Parameters for rotation gates
    parameters = None
    if gate_type in ["RZ", "RY"]:
        angle = st.sidebar.slider("Angle (radians)", -3.14159, 3.14159, 1.5708, step=0.1)
        parameters = [angle]
    
    # Add gate button
    if st.sidebar.button(f"➕ Add {gate_type} Gate"):
        from orquestra_qre.quantum import QuantumGate
        new_gate = QuantumGate(gate_type, qubits, parameters)
        st.session_state.custom_gates.append(new_gate)
        st.sidebar.success(f"Added {gate_type} gate!")
    
    # Show current circuit
    if st.session_state.custom_gates:
        st.sidebar.write(f"**Current Circuit:** {len(st.session_state.custom_gates)} gates")
        for i, gate in enumerate(st.session_state.custom_gates):
            gate_str = f"{gate.name}({','.join(map(str, gate.qubits))})"
            if gate.parameters:
                gate_str += f" θ={gate.parameters[0]:.2f}"
            st.sidebar.write(f"{i+1}. {gate_str}")
    
    # Circuit actions
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear"):
            st.session_state.custom_gates = []
            st.rerun()
    with col2:
        if st.button("✅ Build") and st.session_state.custom_gates:
            from orquestra_qre.quantum import QuantumCircuit
            custom_circuit = QuantumCircuit(
                custom_num_qubits, 
                st.session_state.custom_gates.copy(), 
                "Custom Circuit"
            )
            st.session_state.current_circuit = custom_circuit
            st.rerun()

# --- Metrics Section ---
st.markdown('<div class="section-bg">', unsafe_allow_html=True)
st.title("⚛️ Orquestra QRE Platform")
st.markdown("**Advanced Quantum Resource Estimation & Circuit Design**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🔬 Circuits Built", len(st.session_state.circuit_library))
with col2:
    st.metric("📊 Estimations", len(st.session_state.estimations_history))
with col3:
    avg_fidelity = np.mean([e['estimated_fidelity'] for e in st.session_state.estimations_history]) * 100 if st.session_state.estimations_history else 0
    st.metric("📈 Avg Fidelity", f"{avg_fidelity:.1f}%")
with col4:
    total_gates = sum([e['gate_count'] for e in st.session_state.estimations_history]) if st.session_state.estimations_history else 0
    st.metric("⚡ Total Gates", total_gates)
st.markdown('</div>', unsafe_allow_html=True)

# --- Main Content Section ---
st.markdown('<div class="section-bg">', unsafe_allow_html=True)
main_col1, main_col2 = st.columns([1, 1])
with main_col1:
    st.header("🔮 Current Circuit")
    
    if 'current_circuit' in st.session_state:
        circuit = st.session_state.current_circuit
        
        # Circuit info
        st.info(f"""
        **Name:** {circuit.name}  
        **Qubits:** {circuit.num_qubits}  
        **Gates:** {len(circuit.gates)}  
        **Depth:** {circuit.get_depth()}
        """)
        
        # Only draw the circuit if qubits <= 25
        if circuit.num_qubits <= 25:
            st.subheader("🎯 Interactive Circuit Diagram")
            
            # Interactive circuit plot (main feature)
            interactive_plot = create_interactive_circuit_plot(circuit)
            st.plotly_chart(interactive_plot, use_container_width=True)
            
            # Text representation toggle
            with st.expander("📋 Text Circuit Diagram"):
                circuit_visual = create_circuit_visual(circuit)
                st.code(circuit_visual, language='text')
        else:
            st.warning("Circuit visualization is disabled for circuits with more than 25 qubits.")
        
        # Gate analysis with filtering
        st.subheader("🔍 Gate Analysis")
        gate_data = []
        for i, gate in enumerate(circuit.gates):
            gate_data.append({
                'Step': i+1,
                'Gate': gate.name,
                'Qubits': ', '.join(map(str, gate.qubits)),
                'Parameters': ', '.join(f'{p:.3f}' for p in (gate.parameters or []))
            })
        
        gate_df = pd.DataFrame(gate_data)
        
        # Gate type filter
        if len(gate_df) > 0:
            gate_types = ['All'] + list(gate_df['Gate'].unique())
            selected_gate = st.selectbox("Filter by Gate Type", gate_types)
            
            if selected_gate != 'All':
                gate_df = gate_df[gate_df['Gate'] == selected_gate]
        
        st.dataframe(gate_df, use_container_width=True)
        
        # Save circuit to library
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save to Library"):
                circuit_data = {
                    'name': circuit.name,
                    'circuit': circuit,
                    'timestamp': pd.Timestamp.now()
                }
                st.session_state.circuit_library.append(circuit_data)
                st.success(f"Saved '{circuit.name}' to library!")
        
        with col2:
            # Generate the estimate using all our new parameters
            if st.button("🔄 Generate Estimate"):
                if st.session_state.show_connectivity_analysis and selected_connectivity_model:
                    estimate = hardware_aware_estimate(
                        circuit, estimator, selected_provider, selected_ec,
                        connectivity_model=selected_connectivity_model,
                        swap_estimator=swap_estimator
                    )
                else:
                    estimate = hardware_aware_estimate(circuit, estimator, selected_provider, selected_ec)
                    
                st.session_state.current_estimate = estimate
                
                # Add more details to the estimation history
                est_dict = estimate.to_dict()
                est_dict['provider'] = selected_provider.name
                est_dict['error_correction'] = selected_ec_code
                est_dict['physical_qubits'] = estimate.physical_qubits
                
                if hasattr(estimate, 'swap_overhead') and estimate.swap_overhead:
                    est_dict['swap_overhead'] = estimate.swap_overhead
                    
                st.session_state.estimations_history.append(est_dict)
                st.rerun()
        
    else:
        st.info("👈 Select a circuit type and click 'Generate Circuit' to start!")

with main_col2:
    st.header("📊 Advanced Resource Analysis")
    
    if 'current_circuit' in st.session_state:
        circuit = st.session_state.current_circuit
        
        # Generate the estimate with connectivity analysis if enabled
        if st.session_state.show_connectivity_analysis and selected_connectivity_model:
            estimate = hardware_aware_estimate(
                circuit, estimator, selected_provider, selected_ec,
                connectivity_model=selected_connectivity_model,
                swap_estimator=swap_estimator
            )
        else:
            estimate = hardware_aware_estimate(
                circuit, estimator, selected_provider, selected_ec
            )
        
        # Add to history if not already there
        if 'current_estimate' not in st.session_state or st.session_state.current_estimate != estimate:
            st.session_state.current_estimate = estimate
            # Save provider and EC info in history
            est_dict = estimate.to_dict()
            est_dict['provider'] = selected_provider.name
            est_dict['error_correction'] = selected_ec_code
            est_dict['physical_qubits'] = estimate.physical_qubits
            
            # Include SWAP overhead information if available
            if hasattr(estimate, 'swap_overhead') and estimate.swap_overhead:
                est_dict['swap_overhead'] = estimate.swap_overhead
                
            if not any(e['circuit_name'] == estimate.circuit_name and 
                      e['gate_count'] == estimate.gate_count and
                      e.get('provider') == selected_provider.name and
                      e.get('error_correction') == selected_ec_code
                      for e in st.session_state.estimations_history):
                st.session_state.estimations_history.append(est_dict)
        
        # Show hardware warnings
        if hasattr(estimate, 'hardware_warnings') and estimate.hardware_warnings:
            for w in estimate.hardware_warnings:
                st.warning(w)
        
        # Show metrics vertically (no columns)
        st.metric("⏱️ Runtime (ms)", f"{estimate.estimated_runtime_ms:.1f}")
        st.metric("🎯 Fidelity", f"{estimate.estimated_fidelity*100:.1f}%")
        st.metric("⚡ Gate Count", estimate.gate_count)
        st.metric("📏 Depth", estimate.depth)
        st.metric("🧩 Physical Qubits", estimate.physical_qubits)
        st.metric("🏭 Provider", selected_provider.name)
        st.metric("🛡️ Error Correction", selected_ec_code)

        # Interactive gate breakdown visualization
        st.subheader("🔬 Gate Distribution Analysis")
        if estimate.gate_breakdown:
            tab1, tab2 = st.tabs(["🥧 Pie Chart", "📊 Bar Chart"])
            
            with tab1:
                # Pie chart for gate breakdown
                gate_names = list(estimate.gate_breakdown.keys())
                gate_counts = list(estimate.gate_breakdown.values())
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=gate_names,
                    values=gate_counts,
                    hole=0.4,
                    textinfo='label+percent+value',
                    textfont_size=12,
                    marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#F39C12', '#E74C3C']
                )])
                
                fig_pie.update_layout(
                    title="Gate Type Distribution",
                    height=400,
                    showlegend=True
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with tab2:
                # Bar chart 
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=gate_names,
                        y=gate_counts,
                        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#F39C12', '#E74C3C'],
                        text=gate_counts,
                        textposition='auto'
                    )
                ])
                fig_bar.update_layout(
                    title="Gate Count by Type",
                    xaxis_title="Gate Type",
                    yaxis_title="Count",
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Advanced quantum metrics
        with st.expander("🔬 Advanced Quantum Metrics"):
            st.markdown("**📐 Circuit Properties**")
            st.json({
                "Quantum Volume": f"2^{estimate.num_qubits} = {2**estimate.num_qubits}",
                "T-Gate Count": estimate.gate_breakdown.get('T', 0),
                "CNOT Count": estimate.gate_breakdown.get('CNOT', 0),
                "Circuit Width": estimate.num_qubits,
                "Gate Density": f"{estimate.gate_count/estimate.depth:.2f}"
            })
            
            # Add SWAP analysis section if connectivity analysis is enabled
            if st.session_state.show_connectivity_analysis and hasattr(estimate, 'swap_overhead') and estimate.swap_overhead:
                st.markdown("**🔄 SWAP Overhead Analysis**")
                swap_data = estimate.swap_overhead
                
                # Don't display if there was an error
                if 'error' not in swap_data:
                    st.json({
                        "Non-local CNOTs": swap_data['non_local_cnots'],
                        "Approx. SWAP gates": swap_data['approx_swap_count'],
                        "Additional CNOTs from SWAPs": swap_data['additional_cnots_from_swaps'],
                        "Total gates after routing": swap_data['routed_gate_count'],
                        "Routing factor": f"{swap_data['routing_factor']:.2f}x",
                        "Depth increase": swap_data['swap_depth_overhead']
                    })
                    
                    # Add a visualization of SWAP impact
                    st.markdown("**SWAP Impact on Gate Count:**")
                    fig_swap = go.Figure()
                    
                    # Original vs Routed gate counts
                    fig_swap.add_trace(go.Bar(
                        x=['Original', 'Routed'],
                        y=[swap_data['original_gate_count'], swap_data['routed_gate_count']],
                        marker_color=['#4ECDC4', '#FF6B6B'],
                        text=[swap_data['original_gate_count'], swap_data['routed_gate_count']],
                        textposition='auto'
                    ))
                    
                    fig_swap.update_layout(
                        title="Gate Count Before vs After SWAP Insertion",
                        height=300
                    )
                    
                    st.plotly_chart(fig_swap, use_container_width=True)
            
            st.markdown("**⚡ Performance Estimates**")
            single_qubit_gates = sum(count for gate, count in estimate.gate_breakdown.items() 
                                   if gate in ['H', 'X', 'Y', 'Z', 'RZ', 'RY', 'T', 'S'])
            error_rate = (1-estimate.estimated_fidelity)*100
            st.json({
                "Single Qubit Gates": single_qubit_gates,
                "Error Rate": f"{error_rate:.3f}%",
                "Est. Memory": f"{estimate.gate_count * 0.1:.1f} KB",
                "Decoherence Time": f"{estimate.estimated_runtime_ms * 2:.1f} μs",
                "Success Probability": f"{estimate.estimated_fidelity:.4f}"
            })
        
        # Add real hardware execution section if backend is selected
        if selected_backend:
            st.subheader("🚀 Execute on Real Hardware")
            
            # Execution parameters
            shots_col, opt_col = st.columns(2)
            with shots_col:
                shots = st.number_input("Shots", min_value=1, max_value=10000, value=1000)
            with opt_col:
                optimization_level = st.slider("Optimization Level", 0, 3, 1)
            
            # Execute button
            if st.button("🚀 Submit to Hardware"):
                # Check if credentials are set
                provider_creds = backend_manager.credentials.get(selected_provider_name)
                if not provider_creds or not provider_creds.validate():
                    st.error(f"Please set valid API token for {selected_provider_name} first!")
                else:
                    try:
                        with st.spinner(f"Submitting circuit to {selected_backend}..."):
                            # Submit the job
                            job_id = backend_manager.execute_circuit(
                                circuit,
                                selected_backend,
                                shots=shots,
                                optimization_level=optimization_level
                            )
                            
                            # Add to job history
                            job_info = {
                                'job_id': job_id,
                                'circuit_name': circuit.name,
                                'backend_name': selected_backend,
                                'provider': selected_provider_name,
                                'shots': shots,
                                'submission_time': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'status': 'SUBMITTED'
                            }
                            st.session_state.jobs_history.append(job_info)
                            
                            st.success(f"Job submitted successfully! Job ID: {job_id}")
                    except Exception as e:
                        st.error(f"Error submitting job: {str(e)}")
            
            # Show job history
            if st.session_state.jobs_history:
                with st.expander("📋 Job History"):
                    job_df = pd.DataFrame(st.session_state.jobs_history)
                    st.dataframe(job_df)
                    
                    # Job status refresh and result fetching
                    if st.button("🔄 Refresh Job Status"):
                        updated_jobs = []
                        for job in st.session_state.jobs_history:
                            try:
                                status = backend_manager.get_job_status(job['job_id'], job['backend_name'])
                                job['status'] = status['status']
                                if status['status'] == 'COMPLETED':
                                    job['execution_time'] = status['execution_time']
                                updated_jobs.append(job)
                            except Exception:
                                updated_jobs.append(job)
                        st.session_state.jobs_history = updated_jobs
                        st.rerun()
                    
                    # Results section for completed jobs
                    completed_jobs = [j for j in st.session_state.jobs_history if j['status'] == 'COMPLETED']
                    if completed_jobs:
                        st.subheader("🧪 Job Results")
                        selected_job_idx = st.selectbox(
                            "Select completed job",
                            range(len(completed_jobs)),
                            format_func=lambda i: f"{completed_jobs[i]['circuit_name']} ({completed_jobs[i]['job_id']})"
                        )
                        
                        if st.button("📊 View Results"):
                            selected_job = completed_jobs[selected_job_idx]
                            with st.spinner("Fetching results..."):
                                try:
                                    result = backend_manager.get_job_result(
                                        selected_job['job_id'],
                                        selected_job['backend_name']
                                    )
                                    
                                    if result.success:
                                        # Create bar chart of measurement results
                                        counts = result.counts
                                        fig = go.Figure(data=[go.Bar(
                                            x=list(counts.keys()),
                                            y=list(counts.values()),
                                            marker_color='indigo'
                                        )])
                                        fig.update_layout(
                                            title=f"Measurement Results ({result.job_id})",
                                            xaxis_title="Bitstring",
                                            yaxis_title="Count",
                                            height=400
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Show result details
                                        st.json({
                                            "job_id": result.job_id,
                                            "backend": result.backend_name,
                                            "execution_time_ms": result.execution_time_ms,
                                            "readout_fidelity": result.readout_fidelity,
                                            "shots": result.metadata.get('shots', 0)
                                        })
                                    else:
                                        st.error(f"Error in results: {result.error_message}")
                                except Exception as e:
                                    st.error(f"Error fetching results: {str(e)}")
        
        # Performance comparison with history
        if len(st.session_state.estimations_history) > 1:
            st.subheader("📈 Performance Trends")
            comparison_fig = create_resource_comparison_chart(st.session_state.estimations_history)
            if comparison_fig:
                st.plotly_chart(comparison_fig, use_container_width=True)
    
    else:
        st.info("👈 Generate or build a circuit to see resource estimation!")
        
        # Show estimation history if available
        if st.session_state.estimations_history:
            st.subheader("📋 Recent Estimations")
            recent_df = pd.DataFrame(st.session_state.estimations_history[-5:])  # Last 5
            display_df = recent_df[['circuit_name', 'estimated_runtime_ms', 'estimated_fidelity', 'gate_count']].copy()
            display_df['estimated_fidelity'] = (display_df['estimated_fidelity'] * 100).round(1)
            display_df.columns = ['Circuit', 'Runtime (ms)', 'Fidelity (%)', 'Gates']
            st.dataframe(display_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Circuit Library Section ---
if st.session_state.circuit_library:
    st.markdown('<div class="section-bg">', unsafe_allow_html=True)
    st.header("📚 Circuit Library")
    
    lib_col1, lib_col2 = st.columns([2, 1])
    with lib_col1:
        library_df = pd.DataFrame([{
            'Name': item['name'],
            'Qubits': item['circuit'].num_qubits,
            'Gates': len(item['circuit'].gates),
            'Created': item['timestamp'].strftime('%Y-%m-%d %H:%M')
        } for item in st.session_state.circuit_library])
        
        selected_circuit_idx = st.selectbox(
            "Select circuit from library", 
            range(len(library_df)),
            format_func=lambda i: f"{library_df.iloc[i]['Name']} ({library_df.iloc[i]['Gates']} gates)"
        )
    
    with lib_col2:
        if st.button("🔄 Load Circuit"):
            selected_circuit = st.session_state.circuit_library[selected_circuit_idx]['circuit']
            st.session_state.current_circuit = selected_circuit
            st.rerun()
        
        if st.button("🗑️ Clear Library"):
            st.session_state.circuit_library = []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.markdown("<center>🚀 <b>Built with Streamlit & Plotly</b> | ⚛️ <b>Orquestra QRE Platform</b> | 📊 <b>Interactive Quantum Resource Estimation</b></center>", unsafe_allow_html=True)
