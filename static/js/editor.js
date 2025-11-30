const state = {
    qubits: 3,
    steps: 20,
    gates: [], // { type, target, step, control? }
    draggedType: null,
    pendingOp: null // { type: 'CNOT' | 'SWAP', target, step }
};

const editor = document.getElementById('editor');
const output = document.getElementById('output');
const loading = document.getElementById('loading');

function init() {
    // Initialize state from task if available
    if (window.currentTask && window.currentTask.qubits) {
        state.qubits = window.currentTask.qubits;
    }

    setupPalette();
    setupControls();
    setupModalListeners();
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
        
        // Mouse Drag Events
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

        // Touch Drag Events
        btn.addEventListener('touchstart', handleTouchStart, {passive: false});
        btn.addEventListener('touchmove', handleTouchMove, {passive: false});
        btn.addEventListener('touchend', handleTouchEnd);
        btn.addEventListener('touchcancel', handleTouchEnd);
    });
}

// --- Touch Support ---
let touchDragEl = null;
let touchStartX = 0;
let touchStartY = 0;

function handleTouchStart(e) {
    e.preventDefault(); // Prevent scrolling
    const touch = e.touches[0];
    const btn = e.currentTarget;
    
    state.draggedType = btn.dataset.type;
    editor.classList.add('dragging-active');

    // Create ghost element
    touchDragEl = btn.cloneNode(true);
    touchDragEl.style.position = 'fixed';
    touchDragEl.style.zIndex = '1000';
    touchDragEl.style.opacity = '0.8';
    touchDragEl.style.pointerEvents = 'none'; // Allow elementFromPoint to see through
    touchDragEl.style.width = btn.offsetWidth + 'px';
    touchDragEl.style.height = btn.offsetHeight + 'px';
    
    // Center on finger
    updateTouchPosition(touch.clientX, touch.clientY);
    
    document.body.appendChild(touchDragEl);
}

function handleTouchMove(e) {
    e.preventDefault();
    if (!touchDragEl) return;
    const touch = e.touches[0];
    updateTouchPosition(touch.clientX, touch.clientY);
    
    // Optional: Highlight drop zone
    const target = document.elementFromPoint(touch.clientX, touch.clientY);
    const zone = target ? target.closest('.drop-zone') : null;
    
    document.querySelectorAll('.drop-zone.drag-over').forEach(el => el.classList.remove('drag-over'));
    if (zone) {
        zone.classList.add('drag-over');
    }
}

function handleTouchEnd(e) {
    if (!touchDragEl) return;
    const touch = e.changedTouches[0];
    
    // Find drop target
    const target = document.elementFromPoint(touch.clientX, touch.clientY);
    const zone = target ? target.closest('.drop-zone') : null;

    if (zone) {
        const qubit = parseInt(zone.dataset.qubit);
        const step = parseInt(zone.dataset.step);
        handleDrop(null, qubit, step); // Pass null for event since we prevented default already
    }

    // Cleanup
    document.body.removeChild(touchDragEl);
    touchDragEl = null;
    editor.classList.remove('dragging-active');
    state.draggedType = null;
    document.querySelectorAll('.drop-zone.drag-over').forEach(el => el.classList.remove('drag-over'));
}

function updateTouchPosition(x, y) {
    if (touchDragEl) {
        touchDragEl.style.left = (x - touchDragEl.offsetWidth / 2) + 'px';
        touchDragEl.style.top = (y - touchDragEl.offsetHeight / 2) + 'px';
    }
}
// --- End Touch Support ---

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
        state.pendingOp = null;
        render();
        output.innerHTML = '<div class="placeholder">Run simulation to see results...</div>';
    };
    document.getElementById('simulate').onclick = callBackend;
}

function setupModalListeners() {
    const slider = document.getElementById('angle-slider');
    const input = document.getElementById('angle-input');
    const presets = document.querySelectorAll('.preset-buttons button');

    if (!slider || !input) return;

    // Sync Slider -> Input
    slider.addEventListener('input', () => {
        input.value = slider.value;
    });

    // Sync Input -> Slider
    input.addEventListener('input', () => {
        slider.value = input.value;
    });

    // Presets
    presets.forEach(btn => {
        btn.addEventListener('click', () => {
            const val = btn.getAttribute('data-val');
            slider.value = val;
            input.value = val;
        });
    });
}

function openRotationModal(defaultValue) {
    return new Promise((resolve) => {
        const modal = document.getElementById('rotation-modal');
        const slider = document.getElementById('angle-slider');
        const input = document.getElementById('angle-input');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');

        // Set initial values
        slider.value = defaultValue;
        input.value = defaultValue;
        
        modal.classList.remove('hidden');

        // We need named functions to remove them later
        function onConfirm() {
            const val = parseFloat(input.value);
            cleanup();
            resolve(isNaN(val) ? 0 : val);
        }

        function onCancel() {
            cleanup();
            resolve(null);
        }

        function cleanup() {
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            modal.classList.add('hidden');
        }

        // Add listeners
        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
    });
}

function updateQubitCount() {
    document.getElementById('qubit-count').textContent = state.qubits;
}

function handleDrop(e, qubit, step) {
    if (e) e.preventDefault();
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
        state.pendingOp = { type: 'CNOT', target: qubit, step: step };
        // Temporarily add incomplete gate
        state.gates.push({ type: 'CNOT', target: qubit, step: step, control: null });
        render();
    } else if (type === 'SWAP') {
        state.pendingOp = { type: 'SWAP', target: qubit, step: step };
        // Temporarily add incomplete gate
        state.gates.push({ type: 'SWAP', target: qubit, step: step, params: { other: null } });
        render();
    } else if (['RX', 'RY', 'RZ'].includes(type)) {
        openRotationModal(1.57).then(theta => {
            if (theta !== null) {
                state.gates.push({ type: type, target: qubit, step: step, params: { theta } });
                render();
            }
        });
    } else {
        state.gates.push({ type: type, target: qubit, step: step });
        render();
    }
}

function handleZoneClick(qubit, step) {
    // If we are in pendingOp mode
    if (state.pendingOp) {
        if (state.pendingOp.step !== step) {
            // Clicked wrong column, cancel
            cancelPendingOp();
            return;
        }
        if (state.pendingOp.target === qubit) {
            alert("Target cannot be the same as source.");
            return;
        }

        // Finalize Operation
        const op = state.pendingOp;
        const gate = state.gates.find(g => g.target === op.target && g.step === op.step && g.type === op.type);
        
        if (gate) {
            if (op.type === 'CNOT') {
                gate.control = qubit;
            } else if (op.type === 'SWAP') {
                gate.params = { other: qubit };
            }
        }
        state.pendingOp = null;
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

    // Check if it's a control point or swap partner
    const controlGateIndex = state.gates.findIndex(g => 
        (g.control === qubit && g.step === step) || 
        (g.type === 'SWAP' && g.params && g.params.other === qubit && g.step === step)
    );
    if (controlGateIndex !== -1) {
        state.gates.splice(controlGateIndex, 1);
        render();
    }
}

function cancelPendingOp() {
    if (!state.pendingOp) return;
    const op = state.pendingOp;
    // Remove the incomplete gate
    state.gates = state.gates.filter(g => !(g.target === op.target && g.step === op.step && g.type === op.type && (g.control === null || (g.params && g.params.other === null))));
    state.pendingOp = null;
    render();
}

function render() {
    editor.innerHTML = '';

    if (state.pendingOp) {
        const banner = document.createElement('div');
        banner.style.background = 'rgba(16, 185, 129, 0.2)';
        banner.style.color = '#6ee7b7';
        banner.style.padding = '10px';
        banner.style.textAlign = 'center';
        banner.style.borderRadius = '4px';
        banner.style.marginBottom = '10px';
        banner.style.fontWeight = 'bold';
        if (state.pendingOp.type === 'CNOT') {
            banner.textContent = 'Select a Control Qubit (click a green zone)';
        } else {
            banner.textContent = 'Select the second qubit to SWAP with (click a green zone)';
        }
        editor.appendChild(banner);
    }

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
                
                if (gate.params && gate.params.theta !== undefined) {
                     el.style.fontSize = '0.7em';
                     el.style.display = 'flex';
                     el.style.alignItems = 'center';
                     el.style.justifyContent = 'center';
                     el.textContent = `${gate.type}\n(${gate.params.theta.toFixed(1)})`;
                }

                if (gate.type === 'CNOT' && gate.control === null) {
                    el.style.opacity = '0.5';
                    el.textContent = '?';
                    el.title = "Click a control qubit in this column";
                }
                
                if (gate.type === 'SWAP' && (gate.params === undefined || gate.params.other === null)) {
                    el.style.opacity = '0.5';
                    el.textContent = '?';
                    el.title = "Click another qubit in this column to swap with";
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

            // Render SWAP partner if exists
            const swapGate = state.gates.find(g => g.type === 'SWAP' && g.params && g.params.other === q && g.step === s);
            if (swapGate) {
                const el = document.createElement('div');
                el.className = 'placed-gate';
                el.textContent = 'SWAP';
                // We can style it slightly differently or just rely on the line connecting them
                el.title = `Swapping with q${swapGate.target}`;
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
        } else if (g.type === 'SWAP' && g.params && g.params.other !== null && g.params.other !== undefined) {
            const q1 = g.target;
            const q2 = g.params.other;
            const step = g.step;

            const z1 = container.querySelector(`.drop-zone[data-qubit="${q1}"][data-step="${step}"]`);
            const z2 = container.querySelector(`.drop-zone[data-qubit="${q2}"][data-step="${step}"]`);

            if (z1 && z2) {
                const r1 = z1.getBoundingClientRect();
                const r2 = z2.getBoundingClientRect();

                const x1 = r1.left + r1.width / 2 - containerRect.left;
                const y1 = r1.top + r1.height / 2 - containerRect.top;
                const x2 = r2.left + r2.width / 2 - containerRect.left;
                const y2 = r2.top + r2.height / 2 - containerRect.top;

                // Draw Line
                const line = document.createElementNS(svgNS, "line");
                line.setAttribute("x1", x1);
                line.setAttribute("y1", y1);
                line.setAttribute("x2", x2);
                line.setAttribute("y2", y2);
                line.setAttribute("class", "cnot-line"); // Reuse CNOT line style or create new
                line.style.stroke = "#3b82f6"; // Blue for SWAP
                svg.appendChild(line);

                // We don't need dots for SWAP, the 'x' symbols in the boxes are enough.
                // But maybe we want to ensure the line connects them nicely.
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
            .filter(g => !(g.type === 'CNOT' && g.control === null) && !(g.type === 'SWAP' && (g.params === undefined || g.params.other === null))) // Filter incomplete CNOTs and SWAPs
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
            headers: { 'Content-Type': 'application/json' },
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

                // Render Bloch Spheres
                if (data.statevector) {
                    renderBlochSpheres(data.statevector, state.qubits);
                }
                
                // Validate Task
                if (typeof validateTask === 'function') {
                    validateTask(data);
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
                backgroundColor: 'rgba(146, 112, 82, 0.6)',
                borderColor: '#927052',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' },
                    title: {
                        display: true,
                        text: 'Probability (%)',
                        color: '#94a3b8'
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    titleColor: '#f8fafc',
                    bodyColor: '#f8fafc',
                    backgroundColor: '#1e293b',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            }
        }
    });
}

// --- Bloch Sphere Logic ---

function parseComplex(str) {
    // Format: (real+imagj) or (real-imagj)
    // Remove ()
    str = str.replace(/[()]/g, '');
    let real = 0;
    let imag = 0;

    // Handle 'j' at the end
    if (str.endsWith('j')) {
        str = str.slice(0, -1); // remove j
    } else {
        // Real number only?
        return { re: parseFloat(str), im: 0 };
    }

    // Find the last + or - to split
    // But be careful of scientific notation e.g. 1e-5
    // And the first sign

    // Easier approach: use regex
    // Matches: (real part)(sign)(imag part)
    // But python complex str is a bit tricky: 1+2j, 1-2j, 1j, -1j

    // Let's try a simpler split
    const parts = str.split(/(?=[+-])/);
    // parts might be ["1", "+2"] or ["-1", "-2"]

    parts.forEach(p => {
        if (!p) return;
        if (p === '+' || p === '-') return; // shouldn't happen with lookahead

        let val = parseFloat(p);
        if (isNaN(val)) {
            // maybe just "j" or "-j"? Python outputs 1j usually
            if (p === 'j' || p === '+j') val = 1;
            else if (p === '-j') val = -1;
        }

        // In Python str(complex), the imaginary part is always last and has 'j' (we removed it)
        // Actually we removed 'j' from the very end of the whole string.
        // So if we are processing the last part, it was the imaginary part.

        // Wait, let's restart parsing to be robust.
        // Python: (1+2j) -> 1+2j
    });

    // Robust parsing of Python complex string
    // It's usually (r+ij)
    const match = str.match(/^([+-]?[\d\.eE]+)?([+-]?[\d\.eE]+)?$/);
    // This is getting complicated. Let's assume standard format.

    // Let's just use a simple parser assuming "real+imag" structure
    let s = str;
    let re = 0, im = 0;

    // Find split index
    let splitIdx = -1;
    // Start from end, skip last char (which was j)
    for (let i = s.length - 1; i > 0; i--) {
        if (s[i] === '+' || s[i] === '-') {
            // Check if it's e-5 or e+5
            if (s[i - 1] === 'e' || s[i - 1] === 'E') continue;
            splitIdx = i;
            break;
        }
    }

    if (splitIdx === -1) {
        // Pure imaginary or pure real?
        // We stripped 'j' from end. If it was there, it's imaginary.
        // But we don't know if 'j' was there in this scope.
        // Let's pass the original string with 'j' to this function.
        return { re: 0, im: 0 }; // Fallback
    }

    re = parseFloat(s.substring(0, splitIdx));
    im = parseFloat(s.substring(splitIdx));
    return { re, im };
}

function parseComplexPython(str) {
    // str is like "(0.7071067811865476+0j)"
    str = str.replace(/[()]/g, '');

    // Check for 'j'
    if (!str.includes('j')) {
        return { re: parseFloat(str), im: 0 };
    }

    // Remove 'j'
    str = str.replace('j', '');

    // Find the separator between real and imag
    // Scan from right to left to find + or - that is NOT part of scientific notation
    let sep = -1;
    for (let i = str.length - 1; i > 0; i--) {
        if (str[i] === '+' || str[i] === '-') {
            const prev = str[i - 1].toLowerCase();
            if (prev !== 'e') {
                sep = i;
                break;
            }
        }
    }

    if (sep === -1) {
        // Pure imaginary e.g. "1j" -> "1"
        return { re: 0, im: parseFloat(str) };
    }

    const reStr = str.substring(0, sep);
    const imStr = str.substring(sep);

    return { re: parseFloat(reStr), im: parseFloat(imStr) };
}

function getBlochVector(qubit, nQubits, statevector) {
    // Calculate <X>, <Y>, <Z> for the given qubit
    let x = 0, y = 0, z = 0;

    // Iterate over all basis states
    const N = 1 << nQubits;

    for (let i = 0; i < N; i++) {
        // Get amplitude alpha_i
        const amp = parseComplexPython(statevector[i]);

        // Check if k-th bit is 0 or 1
        // qubit 0 is usually the last bit in binary string (Little Endian? Cirq uses Big Endian by default for printing but let's check)
        // Cirq state vector is usually Big Endian (q0 is MSB? No, usually q0 is first in tensor product)
        // Let's assume standard order: |q0 q1 ... qn>
        // So q0 is the MSB (index 0).
        // i = b0 b1 ... bn
        // bit val is (i >> (nQubits - 1 - qubit)) & 1

        const shift = nQubits - 1 - qubit;
        const bit = (i >> shift) & 1;

        // <Z> calculation
        // If bit is 0, contrib is |amp|^2
        // If bit is 1, contrib is -|amp|^2
        const magSq = amp.re * amp.re + amp.im * amp.im;
        z += (bit === 0 ? 1 : -1) * magSq;

        // For X and Y, we need pairs (i, j) where i has bit 0 and j has bit 1
        if (bit === 0) {
            const j = i | (1 << shift);
            const ampJ = parseComplexPython(statevector[j]);

            // <X>: 2 * Re(amp_i * conj(amp_j)) ??
            // Wait, formula: <psi|X|psi> = sum_k psi_k* (X psi)_k
            // X flips bit. (X psi)_i = psi_j
            // term i: psi_i* psi_j
            // term j: psi_j* psi_i
            // Sum = psi_i* psi_j + psi_j* psi_i = 2 Re(psi_i* psi_j)
            // psi_i * psi_j = (re_i - i im_i) * (re_j + i im_j)
            // = (re_i re_j + im_i im_j) + i(re_i im_j - im_i re_j)
            // We want conjugate of i times j?
            // psi_i* = re_i - i im_i
            // psi_i* psi_j = (re_i - i im_i)(re_j + i im_j)
            // Real part: re_i re_j + im_i im_j

            x += 2 * (amp.re * ampJ.re + amp.im * ampJ.im);

            // <Y>: 2 * Im(psi_i* psi_j)
            // Y|0> = i|1>, Y|1> = -i|0>
            // (Y psi)_i = -i psi_j
            // (Y psi)_j = i psi_i
            // term i: psi_i* (-i psi_j) = -i psi_i* psi_j
            // term j: psi_j* (i psi_i) = i psi_j* psi_i
            // Sum = i (psi_j* psi_i - psi_i* psi_j)
            // Let z = psi_i* psi_j. Then psi_j* psi_i = z*
            // i (z* - z) = i (-2i Im(z)) = 2 Im(z)
            // So we need 2 * Im(psi_i* psi_j)
            // Im(psi_i* psi_j) = re_i im_j - im_i re_j

            y += 2 * (amp.re * ampJ.im - amp.im * ampJ.re);
        }
    }
    return { x, y, z };
}

function renderBlochSpheres(statevector, nQubits) {
    const container = document.getElementById('bloch-container');
    container.innerHTML = '';

    for (let q = 0; q < nQubits; q++) {
        const vec = getBlochVector(q, nQubits, statevector);
        
        const wrapper = document.createElement('div');
        wrapper.className = 'bloch-wrapper';
        wrapper.style.textAlign = 'center';

        const canvas = document.createElement('canvas');
        canvas.width = 200;
        canvas.height = 200;
        wrapper.appendChild(canvas);

        const label = document.createElement('div');
        label.textContent = `Qubit ${q}`;
        wrapper.appendChild(label);

        container.appendChild(wrapper);

        drawBlochSphere(canvas, vec);
    }
}

function drawBlochSphere(canvas, vec) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = w * 0.35;

    ctx.clearRect(0, 0, w, h);

    // Helper to project 3D (x,y,z) to 2D canvas (u,v)
    // Coordinate system:
    // Z is UP (canvas -y)
    // Y is RIGHT (canvas +x)
    // X is FRONT-LEFT (diagonal)
    function project(x, y, z) {
        const u = cx + y * r - x * r * 0.5;
        const v = cy - z * r + x * r * 0.3;
        return { u, v };
    }

    // Draw sphere background
    const grad = ctx.createRadialGradient(cx - r/3, cy - r/3, r/10, cx, cy, r);
    grad.addColorStop(0, '#f8fafc');
    grad.addColorStop(1, '#e2e8f0');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#cbd5e1';
    ctx.stroke();

    // Draw Equator (approximate ellipse)
    ctx.beginPath();
    ctx.ellipse(cx, cy, r, r * 0.3, -0.2, 0, 2 * Math.PI); // Slight tilt
    ctx.strokeStyle = '#dae1e7';
    ctx.stroke();

    // Draw Back Axes (behind the vector if possible, but we just draw first)
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#94a3b8';
    
    // Z Axis (dashed for negative?)
    ctx.beginPath();
    ctx.moveTo(cx, cy - r);
    ctx.lineTo(cx, cy + r);
    ctx.stroke();
    // Label Z
    ctx.fillStyle = '#64748b';
    ctx.font = '12px sans-serif';
    ctx.fillText('|0⟩', cx - 15, cy - r - 5);
    ctx.fillText('|1⟩', cx - 15, cy + r + 15);

    // Y Axis
    const pY = project(0, 1, 0);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(pY.u, pY.v);
    ctx.stroke();
    ctx.fillText('+Y', pY.u + 5, pY.v);

    // X Axis
    const pX = project(1, 0, 0);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(pX.u, pX.v);
    ctx.stroke();
    ctx.fillText('+X', pX.u - 20, pX.v + 10);

    // Draw Vector
    const tip = project(vec.x, vec.y, vec.z);
    
    // Shadow/Line
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(tip.u, tip.v);
    ctx.strokeStyle = '#ea580c'; // Orange-600
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Tip point
    ctx.beginPath();
    ctx.arc(tip.u, tip.v, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#ea580c';
    ctx.fill();
    
    // Debug info
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px monospace';
    ctx.fillText(`x:${vec.x.toFixed(2)}`, 10, h - 35);
    ctx.fillText(`y:${vec.y.toFixed(2)}`, 10, h - 20);
    ctx.fillText(`z:${vec.z.toFixed(2)}`, 10, h - 5);
}

// Init
init();

// --- Task Validation & Progress ---

function validateTask(data) {
    if (!window.currentTask) return;
    
    const task = window.currentTask;
    const criteria = task.criteria;
    let success = false;
    let message = "";

    if (criteria === 'superposition') {
        // Check if probabilities are roughly 50/50 for 0 and 1
        // Assuming 1 qubit for now as per task description
        if (data.probabilities && data.probabilities.length >= 2) {
            const p0 = data.probabilities[0];
            const p1 = data.probabilities[1];
            if (Math.abs(p0 - 0.5) < 0.1 && Math.abs(p1 - 0.5) < 0.1) {
                success = true;
                message = "Great job! You created a superposition.";
            } else {
                message = `Not quite. Probabilities are ${Math.round(p0*100)}% and ${Math.round(p1*100)}%. Aim for 50/50.`;
            }
        }
    } else if (criteria === 'bell_pair') {
        // Check for |00> and |11> with ~50% prob each
        // |00> is index 0, |11> is index 3 (binary 11)
        if (data.probabilities && data.probabilities.length >= 4) {
             const p00 = data.probabilities[0];
             const p11 = data.probabilities[3];
             const p01 = data.probabilities[1];
             const p10 = data.probabilities[2];
             
             if (Math.abs(p00 - 0.5) < 0.1 && Math.abs(p11 - 0.5) < 0.1 && p01 < 0.01 && p10 < 0.01) {
                 success = true;
                 message = "Excellent! You created a Bell Pair entanglement.";
             } else {
                 message = "Close, but not a perfect Bell Pair. Make sure you have 50% |00> and 50% |11>.";
             }
        }
    } else if (criteria === 'rotation_ry_pi_2') {
        // Check if RY gate was used with approx 1.57
        const hasRy = state.gates.some(g => g.type === 'RY' && Math.abs(g.params.theta - 1.57) < 0.1);
        
        // Check probabilities (should be 50/50)
        if (data.probabilities && data.probabilities.length >= 2) {
            const p0 = data.probabilities[0];
            const p1 = data.probabilities[1];
            
            if (hasRy && Math.abs(p0 - 0.5) < 0.1) {
                success = true;
                message = "Perfect! Ry(π/2) creates a superposition just like Hadamard.";
            } else if (!hasRy) {
                message = "Use an Ry gate for this task.";
            } else {
                message = "Check your angle. It should be π/2 (approx 1.57).";
            }
        }
    } else if (criteria === 'eigenvalue_z_1') {
        // Goal: Apply Z to |1> to get -|1>
        // Statevector should be [0, -1] (approx)
        if (data.statevector && data.statevector.length >= 2) {
             const amp0 = parseComplexPython(data.statevector[0]);
             const amp1 = parseComplexPython(data.statevector[1]);
             
             // Check magnitude of 1 is ~1 and 0 is ~0
             const mag0 = Math.sqrt(amp0.re**2 + amp0.im**2);
             const mag1 = Math.sqrt(amp1.re**2 + amp1.im**2);
             
             if (Math.abs(mag1 - 1.0) < 0.1) {
                 // Check phase of amp1. Should be -1 (re ~ -1, im ~ 0)
                 if (Math.abs(amp1.re + 1.0) < 0.1 && Math.abs(amp1.im) < 0.1) {
                     success = true;
                     message = "Correct! The eigenvalue is -1 (phase flip).";
                 } else if (Math.abs(amp1.re - 1.0) < 0.1) {
                     message = "You have the state |1>, but the phase is positive. Did you apply the Z gate?";
                 } else {
                     message = "You have the correct state probability, but the phase is incorrect.";
                 }
             } else {
                 message = "You need to prepare the state |1> first (use X gate).";
             }
        }
    } else if (criteria === 'h_then_x') {
        // Goal: Apply H then X. Result is |+> (50/50)
        const hasH = state.gates.some(g => g.type === 'H');
        const hasX = state.gates.some(g => g.type === 'X');
        
        if (data.probabilities && data.probabilities.length >= 2) {
             const p0 = data.probabilities[0];
             const p1 = data.probabilities[1];
             
             if (hasH && hasX) {
                 if (Math.abs(p0 - 0.5) < 0.1 && Math.abs(p1 - 0.5) < 0.1) {
                     success = true;
                     message = "Correct! X|+> = |+>. The state is unchanged by X.";
                 } else {
                     message = "You have the gates, but the state is not 50/50. Check your circuit.";
                 }
             } else if (!hasH) {
                 message = "First, create a superposition using the H gate.";
             } else if (!hasX) {
                 message = "Now apply the X gate to the superposition.";
             }
        }
    } else if (criteria === 'state_one') {
        // Goal: Transform |0> to |1> using X gate
        if (data.probabilities && data.probabilities.length >= 2) {
             const p0 = data.probabilities[0];
             const p1 = data.probabilities[1];
             
             if (p1 > 0.9 && p0 < 0.1) {
                 success = true;
                 message = "Correct! You transformed |0> to |1> using the X gate.";
             } else if (p0 > 0.9) {
                 message = "You're still in the |0> state. Try applying the X gate.";
             } else {
                 message = "Incorrect state. Aim for |1> (Probability of 1 should be 100%).";
             }
        }
    } else if (criteria === 'minus_state') {
        // Goal: Create |-> = 1/sqrt(2) (|0> - |1>)
        // Use H then Z
        if (data.statevector && data.statevector.length >= 2) {
             const amp0 = parseComplexPython(data.statevector[0]);
             const amp1 = parseComplexPython(data.statevector[1]);
             
             const magSq0 = amp0.re**2 + amp0.im**2;
             const magSq1 = amp1.re**2 + amp1.im**2;
             
             // Check probabilities (0.5 each)
             const probsCorrect = Math.abs(magSq0 - 0.5) < 0.1 && Math.abs(magSq1 - 0.5) < 0.1;
             
             if (probsCorrect) {
                 // Check relative phase difference
                 // angle1 - angle0 should be PI (or -PI)
                 const angle0 = Math.atan2(amp0.im, amp0.re);
                 const angle1 = Math.atan2(amp1.im, amp1.re);
                 let diff = angle1 - angle0;
                 
                 // Normalize to [-PI, PI]
                 while (diff <= -Math.PI) diff += 2*Math.PI;
                 while (diff > Math.PI) diff -= 2*Math.PI;
                 
                 // Check if diff is approx PI or -PI (cos(diff) ~ -1)
                 if (Math.abs(Math.cos(diff) + 1) < 0.1) {
                     success = true;
                     message = "Correct! You created the |-> state. Notice the phase of |1> is flipped.";
                 } else if (Math.abs(Math.cos(diff) - 1) < 0.1) {
                     message = "You have the |+> state. You need to flip the phase of |1>. Try the Z gate.";
                 } else {
                     message = "Probabilities are correct, but the phase difference is not 180 degrees.";
                 }
             } else {
                 message = "First, create a superposition with the H gate, then apply Z.";
             }
        }
    }

    const taskBox = document.getElementById('task-box');
    const taskStatus = document.getElementById('task-status');
    
    if (taskBox && taskStatus) {
        if (success) {
            taskStatus.className = 'status-success';
            taskStatus.textContent = '✅ ' + message;
            saveProgress();
        } else {
            taskStatus.className = 'status-fail';
            taskStatus.textContent = '❌ ' + message;
        }
    }
}

async function saveProgress() {
    if (!window.currentLessonId) return;

    try {
        await fetch('/api/progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lesson_id: window.currentLessonId,
                status: 'completed'
            })
        });
        console.log("Progress saved!");
        if (window.isLoggedIn) {
            setTimeout(() => location.reload(), 1500);
        }
    } catch (e) {
        console.error("Failed to save progress", e);
    }
}
