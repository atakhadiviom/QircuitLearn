const state = {
    qubits: 3,
    steps: 20,
    gates: [], // { type, target, step, control? }
    draggedType: null,
    pendingCNOT: null // { target, step }
};

const editor = document.getElementById('editor');
const output = document.getElementById('output');
const loading = document.getElementById('loading');

function init() {
    setupPalette();
    setupControls();
    updateQubitCount();
    render();
    
    // Update lines on resize
    window.addEventListener('resize', () => {
        const container = document.querySelector('.circuit-grid');
        if (container) {
            updateCircuitLines(container);
        }
    });
}

function setupPalette() {
    document.querySelectorAll('.gate-btn').forEach(btn => {
        btn.setAttribute('draggable', 'true');
        btn.addEventListener('dragstart', (e) => {
            state.draggedType = btn.dataset.type;
            e.dataTransfer.effectAllowed = 'copy';
            e.dataTransfer.setData('text/plain', btn.dataset.type);
            btn.classList.add('dragging');
            editor.classList.add('dragging-active');
        });
        btn.addEventListener('dragend', () => {
            btn.classList.remove('dragging');
            editor.classList.remove('dragging-active');
            state.draggedType = null;
        });
    });
}

function setupControls() {
    document.getElementById('add-qubit').onclick = () => {
        if (state.qubits < 8) {
            state.qubits++;
            updateQubitCount();
            render();
        }
    };
    document.getElementById('remove-qubit').onclick = () => {
        if (state.qubits > 1) {
            state.qubits--;
            // Remove gates on the removed qubit
            state.gates = state.gates.filter(g => g.target < state.qubits && (g.control === undefined || g.control < state.qubits));
            updateQubitCount();
            render();
        }
    };
    document.getElementById('clear').onclick = () => {
        state.gates = [];
        state.pendingCNOT = null;
        render();
        output.innerHTML = '<div class="placeholder">Run simulation to see results...</div>';
    };
    document.getElementById('simulate').onclick = callBackend;
}

function updateQubitCount() {
    document.getElementById('qubit-count').textContent = state.qubits;
}

function handleDrop(e, qubit, step) {
    e.preventDefault();
    const type = state.draggedType;
    if (!type) return;

    // Check if slot is occupied
    const existing = state.gates.find(g => g.target === qubit && g.step === step);
    if (existing) {
        // Replace or ignore? Let's replace.
        state.gates = state.gates.filter(g => g !== existing);
    }
    
    // Also check if this slot is a control for another gate
    const existingControl = state.gates.find(g => g.control === qubit && g.step === step);
    if (existingControl) {
        alert("Cannot place gate here: This qubit is a control for another gate at this step.");
        return;
    }

    if (type === 'CNOT') {
        state.pendingCNOT = { target: qubit, step: step };
        // Temporarily add incomplete gate
        state.gates.push({ type: 'CNOT', target: qubit, step: step, control: null });
        render();
        // Show instruction?
        // alert("Now click the Control qubit for this CNOT.");
    } else {
        state.gates.push({ type: type, target: qubit, step: step });
        render();
    }
}

function handleZoneClick(qubit, step) {
    // If we are in pendingCNOT mode, this click sets the control
    if (state.pendingCNOT) {
        if (state.pendingCNOT.step !== step) {
            // Clicked wrong column, maybe cancel?
            cancelPendingCNOT();
            return;
        }
        if (state.pendingCNOT.target === qubit) {
            alert("Control cannot be the same as target.");
            return;
        }
        
        // Finalize CNOT
        const gate = state.gates.find(g => g.target === state.pendingCNOT.target && g.step === state.pendingCNOT.step && g.type === 'CNOT');
        if (gate) {
            gate.control = qubit;
        }
        state.pendingCNOT = null;
        render();
        return;
    }

    // Otherwise, maybe remove gate if one exists?
    const gateIndex = state.gates.findIndex(g => g.target === qubit && g.step === step);
    if (gateIndex !== -1) {
        state.gates.splice(gateIndex, 1);
        render();
        return;
    }
    
    // Check if it's a control point
    const controlGateIndex = state.gates.findIndex(g => g.control === qubit && g.step === step);
    if (controlGateIndex !== -1) {
        state.gates.splice(controlGateIndex, 1);
        render();
    }
}

function cancelPendingCNOT() {
    if (!state.pendingCNOT) return;
    // Remove the incomplete gate
    state.gates = state.gates.filter(g => !(g.target === state.pendingCNOT.target && g.step === state.pendingCNOT.step && g.type === 'CNOT' && g.control === null));
    state.pendingCNOT = null;
    render();
}

function render() {
    editor.innerHTML = '';
    
    const container = document.createElement('div');
    container.className = 'circuit-grid';
    
    // SVG Container for lines (CNOT connections)
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "circuit-overlay");
    container.appendChild(svg);
    
    for (let q = 0; q < state.qubits; q++) {
        const row = document.createElement('div');
        row.className = 'qubit-row';
        
        const label = document.createElement('div');
        label.className = 'qubit-label';
        label.textContent = `q${q}`;
        row.appendChild(label);
        
        const wireContainer = document.createElement('div');
        wireContainer.className = 'wire-container';
        
        const wireLine = document.createElement('div');
        wireLine.className = 'wire-line';
        wireContainer.appendChild(wireLine);
        
        // Create drop zones for each step
        for (let s = 0; s < state.steps; s++) {
            const zone = document.createElement('div');
            zone.className = 'drop-zone';
            zone.dataset.qubit = q;
            zone.dataset.step = s;
            
            // Drag events
            zone.ondragover = (e) => {
                e.preventDefault(); // Allow drop
                zone.classList.add('drag-over');
            };
            zone.ondragleave = () => {
                zone.classList.remove('drag-over');
            };
            zone.ondrop = (e) => {
                zone.classList.remove('drag-over');
                handleDrop(e, q, s);
            };
            
            // Click handler (remove or set control)
            zone.onclick = () => handleZoneClick(q, s);
            
            // Render Gate if exists
            const gate = state.gates.find(g => g.target === q && g.step === s);
            if (gate) {
                const el = document.createElement('div');
                el.className = 'placed-gate';
                el.textContent = gate.type;
                if (gate.type === 'CNOT' && gate.control === null) {
                    el.style.opacity = '0.5';
                    el.textContent = '?';
                    el.title = "Click a control qubit in this column";
                }
                // Prevent drag on placed gates for now (simple)
                // Or make them draggable to move?
                // Let's keep it simple: Click to delete/move.
                zone.appendChild(el);
            }
            
            // Render Control point if exists
            const controlledGate = state.gates.find(g => g.control === q && g.step === s);
            if (controlledGate) {
                const el = document.createElement('div');
                el.className = 'placed-gate control';
                // Make transparent so SVG dot shows, but keep for interaction
                el.style.opacity = '0'; 
                el.title = `Control for q${controlledGate.target}`;
                zone.appendChild(el);
            }
            
            // Highlight if valid target for pending CNOT
            if (state.pendingCNOT && state.pendingCNOT.step === s && state.pendingCNOT.target !== q) {
                zone.style.background = 'rgba(16, 185, 129, 0.2)'; // Green tint hint
                zone.style.cursor = 'pointer';
            }
            
            wireContainer.appendChild(zone);
        }
        
        row.appendChild(wireContainer);
        container.appendChild(row);
    }
    
    editor.appendChild(container);
    
    // Draw lines after layout
    requestAnimationFrame(() => updateCircuitLines(container));
}

function updateCircuitLines(container) {
    const svg = container.querySelector('.circuit-overlay');
    // Clear existing
    while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
    }
    
    const svgNS = "http://www.w3.org/2000/svg";
    const containerRect = container.getBoundingClientRect();
    
    // Draw lines for CNOTs
    state.gates.forEach(g => {
        if (g.type === 'CNOT' && g.control !== null && g.control !== undefined) {
            const controlQ = g.control;
            const targetQ = g.target;
            const step = g.step;
            
            // Find zones
            const controlZone = container.querySelector(`.drop-zone[data-qubit="${controlQ}"][data-step="${step}"]`);
            const targetZone = container.querySelector(`.drop-zone[data-qubit="${targetQ}"][data-step="${step}"]`);
            
            if (controlZone && targetZone) {
                const cRect = controlZone.getBoundingClientRect();
                const tRect = targetZone.getBoundingClientRect();
                
                const x1 = cRect.left + cRect.width / 2 - containerRect.left;
                const y1 = cRect.top + cRect.height / 2 - containerRect.top;
                const x2 = tRect.left + tRect.width / 2 - containerRect.left;
                const y2 = tRect.top + tRect.height / 2 - containerRect.top;
                
                // Draw Line
                const line = document.createElementNS(svgNS, "line");
                line.setAttribute("x1", x1);
                line.setAttribute("y1", y1);
                line.setAttribute("x2", x2);
                line.setAttribute("y2", y2);
                line.setAttribute("class", "cnot-line");
                svg.appendChild(line);
                
                // Draw Control Dot
                const circle = document.createElementNS(svgNS, "circle");
                circle.setAttribute("cx", x1);
                circle.setAttribute("cy", y1);
                circle.setAttribute("r", "5");
                circle.setAttribute("class", "cnot-control");
                svg.appendChild(circle);
            }
        }
    });
}


let resultsChart = null;

async function callBackend() {
    loading.classList.remove('hidden');
    output.textContent = 'Running...';
    
    // Reset chart
    const chartContainer = document.querySelector('.chart-container');
    chartContainer.style.display = 'none';
    if (resultsChart) {
        resultsChart.destroy();
        resultsChart = null;
    }
    
    try {
        // Sort gates by step
        const sortedGates = [...state.gates]
            .filter(g => !(g.type === 'CNOT' && g.control === null)) // Filter incomplete CNOTs
            .sort((a, b) => a.step - b.step);
            
        const payload = {
            circuit: {
                qubits: state.qubits,
                gates: sortedGates
            },
            shots: 0 // 0 for statevector/probabilities
        };
        
        const res = await fetch('/api/simulate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (data.error) {
            output.textContent = `Error: ${data.error}`;
        } else {
            let outStr = '';
            const labels = [];
            const values = [];
            
            if (data.probabilities) {
                outStr += 'State Vector Probabilities:\n';
                data.probabilities.forEach((p, i) => {
                    // Always add to chart data if it's significant or if we want full range
                    // For chart clarity, let's only show states with > 0.1% probability
                    // unless there are very few states.
                    const bin = i.toString(2).padStart(state.qubits, '0');
                    const pct = (p * 100).toFixed(1);
                    
                    if (p > 0.0001) {
                        outStr += `|${bin}⟩: ${pct}%\n`;
                        labels.push(`|${bin}⟩`);
                        values.push(p * 100);
                    }
                });
                
                // Render Chart
                if (labels.length > 0) {
                    chartContainer.style.display = 'block';
                    renderChart(labels, values);
                }
            } else {
                outStr += JSON.stringify(data, null, 2);
            }
            output.textContent = outStr;
        }
    } catch (e) {
        output.textContent = `Error: ${e.message}`;
    } finally {
        loading.classList.add('hidden');
    }
}

function renderChart(labels, data) {
    const ctx = document.getElementById('resultsChart').getContext('2d');
    resultsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probability (%)',
                data: data,
                backgroundColor: 'rgba(79, 70, 229, 0.6)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Probability (%)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

init();
